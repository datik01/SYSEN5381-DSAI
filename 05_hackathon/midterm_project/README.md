# City Congestion Tracker

This project is an end-to-end AI-powered database pipeline that tracks city traffic congestion, acting as a real-time monitoring and reporting system for a city transportation authority.

It satisfies the requirements for the SYSEN-5381 **Midterm DL Challenge**.

## System Architecture

The pipeline consists of four main components interacting in sequence: **Database &rarr; REST API &rarr; Dashboard &rarr; AI**.

1. **Database (Supabase PostgreSQL)**: 
   - Stores master location data (traffic zones, intersections).
   - Stores time-series data of congestion readings (severity level 1-5).
   - *A synthetic data seed script (`database/seed_data.py`) generates 7 days of realistic historical data based on rush hour patterns.*
2. **REST API (FastAPI / Python)**:
   - Connects to Supabase to fetch location and congestion data.
   - Provides endpoints to retrieve data by location and time.
   - Provides a `POST /congestion/summarize` endpoint which handles the AI integration.
3. **AI Model (Ollama Cloud `gpt-oss:20b-cloud`)**:
   - The API securely aggregates the requested traffic data and sends a prompt to the Ollama Cloud model.
   - The model acts as a "traffic analyst" and returns an actionable, plain-language narrative.
4. **Dashboard (Shiny for Python)**:
   - Provides an interactive UI for city officials.
   - Allows users to slice data by "days back".
   - Visualizes current traffic (bar chart) and historical trends (line chart).
   - Features a "Generate AI Summary" button to quickly fetch insights from the API.

## Repository Structure

```
.
├── .env                       # Environment variables (SUPABASE URL/KEY, OLLAMA_API_KEY)
├── README.md                  # This file
├── CODEBOOK.md                # Describes the data schema and variables
├── database/
│   ├── schema.sql             # SQL table definitions
│   └── seed_data.py           # Synthetic data generation script
├── api/
│   ├── main.py                # FastAPI application
│   ├── requirements.txt       # API dependencies
│   └── manifest.json          # Deployment manifest
└── dashboard/
    ├── app.py                 # Shiny UI & Server
    ├── requirements.txt       # Dashboard dependencies
    └── manifest.json          # Deployment manifest
```

## How to Run Locally

### Prerequisites
1. Ensure you have Python 3.9+ installed.
2. Initialize the Supabase tables using `database/schema.sql` (or via MCP).
3. Ensure your `.env` contains:
   ```env
   SUPABASE_URL=...
   SUPABASE_KEY=...
   OLLAMA_API_KEY=...
   ```

### 1. Seed the Database
```bash
pip install supabase python-dotenv pydantic
python database/seed_data.py
```

### 2. Start the REST API
```bash
cd api
pip install -r requirements.txt
uvicorn main:app --port 8000
```
*The API will be available at `http://127.0.0.1:8000`.*

### 3. Start the Shiny Dashboard
In a new terminal:
```bash
cd dashboard
pip install -r requirements.txt
shiny run app.py --port 8080
```
*The Dashboard will be available at `http://127.0.0.1:8080`.*

## Deployment

Both the `api/` and `dashboard/` directories contain a `manifest.json` file. 
You can link this GitHub repository directly to Posit Connect or use the `rsconnect` CLI to deploy them. 

Once the API is deployed to its production URL, update the `API_BASE_URL` environment variable in Posit Connect for the Dashboard app so they can communicate successfully.
