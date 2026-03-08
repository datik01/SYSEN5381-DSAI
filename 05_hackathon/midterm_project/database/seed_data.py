import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client
from pydantic import BaseModel

# Load environment variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

locations_data = [
    {"name": "Downtown Crossing", "zone": "Central"},
    {"name": "North End Tunnel", "zone": "North"},
    {"name": "Southside Highway", "zone": "South"},
    {"name": "West End Bridge", "zone": "West"},
    {"name": "Eastside Airport Road", "zone": "East"},
]

def seed_database():
    print("Seeding locations...")
    # Insert locations
    locations_response = supabase.table('locations').insert(locations_data).execute()
    inserted_locations = locations_response.data
    
    print(f"Inserted {len(inserted_locations)} locations.")
    
    # Generate 365 days of historical reading per location (every hour)
    now = datetime.now()
    readings = []
    
    for loc in inserted_locations:
        loc_id = loc['id']
        for day in range(365): # Last 365 days
            for hour in range(24): # 24 hours per day
                timestamp = now - timedelta(days=day, hours=hour, minutes=random.randint(0, 59))
                
                # Base severity depends on time of day (rush hour is worse)
                base_severity = 2 # Normal traffic
                if 7 <= timestamp.hour <= 9 or 16 <= timestamp.hour <= 18: # Rush hours
                    base_severity = 4
                elif 0 <= timestamp.hour <= 5: # Night time
                    base_severity = 1
                
                # Add some randomness
                severity = max(1, min(5, base_severity + random.randint(-1, 1)))
                
                readings.append({
                    "location_id": loc_id,
                    "timestamp": timestamp.isoformat(),
                    "severity_level": severity
                })
    
    print(f"Seeding {len(readings)} historical congestion readings...")
    
    # Clear existing readings first to prevent duplicates
    print("Clearing existing data...")
    supabase.table('congestion_readings').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
    
    # Insert in batches of 100
    batch_size = 500
    for i in range(0, len(readings), batch_size):
        batch = readings[i:i + batch_size]
        try:
            supabase.table('congestion_readings').insert(batch).execute()
        except Exception as e:
            print(f"Error on batch {i}: {e}")
            
    print("Database seeding completed securely and successfully!")

if __name__ == "__main__":
    seed_database()
