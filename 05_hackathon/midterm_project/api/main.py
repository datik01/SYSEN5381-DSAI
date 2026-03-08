import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv

import requests

# Load environment variables (will ignore silently if .env doesn't exist in prod)
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)

# Supabase setup
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Missing Supabase credentials in environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Ollama setup
OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")

app = FastAPI(title="City Congestion Tracker API", description="API for monitoring traffic and generating AI insights")

# Allow CORS for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class Location(BaseModel):
    id: str
    name: str
    zone: str

class CongestionReading(BaseModel):
    id: str
    location_id: str
    timestamp: str
    severity_level: int

class InsightRequest(BaseModel):
    location_id: Optional[str] = None
    days_back: int = 7

class InsightResponse(BaseModel):
    summary: str

@app.get("/")
def read_root():
    return {"message": "Welcome to the City Congestion Tracker API"}

@app.get("/locations", response_model=List[Location])
def get_locations():
    """Fetch all monitored traffic zones"""
    response = supabase.table("locations").select("*").execute()
    return response.data

@app.get("/congestion/current")
def get_current_congestion():
    """Fetch the latest congestion reading for each location"""
    # Simply get all recent readings, sort descending by time, we can group logic in client or here.
    # To keep it simple, fetch last few hours and group by location
    two_hours_ago = (datetime.now() - timedelta(hours=2)).isoformat()
    response = supabase.table("congestion_readings").select("*, locations(name, zone)").gte("timestamp", two_hours_ago).order("timestamp", desc=True).execute()
    
    # Get latest reading per location
    latest = {}
    for r in response.data:
        loc_id = r["location_id"]
        if loc_id not in latest:
            latest[loc_id] = {
                "location_id": loc_id,
                "name": r["locations"]["name"],
                "zone": r["locations"]["zone"],
                "timestamp": r["timestamp"],
                "severity_level": r["severity_level"]
            }
    return list(latest.values())

@app.get("/congestion/history")
def get_congestion_history(
    location_id: Optional[str] = Query(None, description="Filter by location ID"),
    days: int = Query(7, description="Number of days to go back")
):
    """Fetch historical time-series data"""
    start_time = (datetime.now() - timedelta(days=days)).isoformat()
    
    query = supabase.table("congestion_readings").select("*, locations(name, zone)").gte("timestamp", start_time)
    
    if location_id:
        query = query.eq("location_id", location_id)
        
    response = query.order("timestamp", desc=False).execute()
    return response.data

@app.post("/congestion/summarize", response_model=InsightResponse)
def generate_insights(request: InsightRequest):
    """Use AI to generate a plain-language summary of recent traffic patterns"""
    if not OLLAMA_API_KEY:
        raise HTTPException(status_code=500, detail="Ollama API key not configured")
        
    # 1. Fetch data
    start_time = (datetime.now() - timedelta(days=request.days_back)).isoformat()
    
    query = supabase.table("congestion_readings").select("severity_level, timestamp, locations(name, zone)").gte("timestamp", start_time)
    if request.location_id:
        query = query.eq("location_id", request.location_id)
        
    response = query.execute()
    data = response.data
    
    if not data:
        return InsightResponse(summary="Not enough data available for the requested period to generate insights.")
        
    # 2. Prepare summary of data to send to AI
    # We shouldn't send 10,000 rows. We'll pre-aggregate a bit.
    severity_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    worst_locations = {}
    
    for r in data:
        level = r.get("severity_level")
        severity_counts[level] = severity_counts.get(level, 0) + 1
        
        if level >= 4:
            loc_name = r["locations"]["name"]
            worst_locations[loc_name] = worst_locations.get(loc_name, 0) + 1
            
    # Top 3 worst locations
    sorted_worst = sorted(worst_locations.items(), key=lambda x: x[1], reverse=True)[:3]
    worst_str = ", ".join([f"{name} ({count} severe readings)" for name, count in sorted_worst])
    
    data_context = f"""
    Time Period: Last {request.days_back} days
    Total Readings: {len(data)}
    Severity Distribution (1=clear, 5=gridlock): 
      - Normal (1-2): {severity_counts[1] + severity_counts[2]} readings
      - Moderate (3): {severity_counts[3]} readings
      - Heavy (4-5): {severity_counts[4] + severity_counts[5]} readings
    Most congested locations (by high-severity reading count): {worst_str if worst_str else 'None'}
    """
    
    # 3. Ask AI for insights
    prompt = f"""
    You are an AI city traffic analyst. I am providing you with aggregated congestion data 
    over the past {request.days_back} days.
    
    Data Summary:
    {data_context}
    
    Please provide a short, actionable narrative summary (3-4 sentences total). 
    Tell the transportation authority what is currently the worst area, how it compares overall, 
    and where they should focus their attention. Use an objective but urgent tone if there is heavy congestion.
    """
    
    try:
        url = "https://ollama.com/api/chat"
        body = {
            "model": "gpt-oss:20b-cloud",
            "messages": [
                {"role": "system", "content": "You are a helpful traffic analysis assistant."},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        }
        headers = {
            "Authorization": f"Bearer {OLLAMA_API_KEY}",
            "Content-Type": "application/json"
        }
        
        response_model = requests.post(url, headers=headers, json=body)
        response_model.raise_for_status()
        
        result = response_model.json()
        summary_text = result["message"]["content"].strip()
        
        return InsightResponse(summary=summary_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate AI insights: {str(e)}")
