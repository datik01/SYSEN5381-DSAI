# CityPulse Congestion Hub (Midterm DL Challenge)

This project is an end-to-end AI-powered database pipeline that monitors, visualizes, and analyzes city traffic congestion.

## Architecture Pipeline

1. **Database Layer (Supabase PostgreSQL)**
   - Houses two relational tables: `locations` (city zones) and `congestion_readings` (hourly severity metrics).
   - A synthetic data generator (`seed_data.py`) populates the database with 365 days of historical traffic data, simulating organic rush-hour and nighttime trends.

2. **REST API Layer (FastAPI)**
   - Acts as the secure middleware between the database and the frontend.
   - Built with FastAPI (`main.py`) and deployed on Posit Connect as an ASGI application.
   - Endpoints include fetching live data, querying historical time-series data, and an AI summarization route.

3. **Dashboard Layer (Shiny for Python)**
   - A modern, glassmorphism-styled web application.
   - Users can drag a slider to fetch up to 1 year of historical data from the API and visualize it using Matplotlib and Seaborn heatmaps.

4. **AI Intelligence Layer (Ollama Cloud / GPT)**
   - When requested via the dashboard, the API aggregates the selected time-horizon data and passes it via a prompt to an AI model (Ollama Cloud).
   - The AI returns an actionable, plain-language narrative identifying the most congested zones and advising transportation authorities.

## Local Setup & Usage

1. **Install Requirements:**
   ```bash
   pip install -r api/requirements.txt
   pip install -r dashboard/requirements.txt
   ```

2. **Environment Variables:**
   Create a `.env` file in the root directory:
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   OLLAMA_API_KEY=your_ollama_key
   ```

3. **Run the API:**
   ```bash
   uvicorn api.main:app --reload --port 8000
   ```

4. **Run the Dashboard:**
   ```bash
   shiny run dashboard/app.py --port 8080
   ```

## Deployment
Both the API and the Dashboard contain `manifest.json` files configured for native deployment to Posit Connect using Python 3.12 environments.

**Live Endpoints:**
- **Dashboard Deployment:** [https://connect.systems-apps.com/content/43ec486d-ba33-41cf-9efe-a318a6cb80c0/](https://connect.systems-apps.com/content/43ec486d-ba33-41cf-9efe-a318a6cb80c0/)
- **API Deployment:** [https://connect.systems-apps.com/content/10263075-06b8-43f3-8dee-a938591f37f2](https://connect.systems-apps.com/content/10263075-06b8-43f3-8dee-a938591f37f2)
