import requests
import pandas as pd
import plotly.express as px
from shiny import App, ui, render, reactive
import os

# API Configuration
API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")

def fetch_locations():
    """
    Fetches the list of all monitored traffic locations from the REST API.
    
    Returns:
        list: A list of dictionaries, where each dictionary represents a location 
              with keys like 'id', 'name', and 'zone'. Returns an empty list on failure.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/locations")
        response.raise_for_status()
        return response.json()
    except:
        return []

def fetch_current_congestion():
    """
    Fetches the most recent live congestion readings for all locations.
    Uses a cache-busting timestamp parameter to ensure the latest data is retrieved.
    
    Returns:
        pd.DataFrame: A pandas DataFrame containing the latest telemetric data with 
                      columns for location details and 'severity_level'.
                      Returns an empty DataFrame if the request fails.
    """
    try:
        import time
        response = requests.get(f"{API_BASE_URL}/congestion/current?t={int(time.time()*1000)}")
        response.raise_for_status()
        return pd.DataFrame(response.json())
    except:
        return pd.DataFrame()

def fetch_historical_congestion(days=7):
    """
    Retrieves historical time-series congestion data over a specified time horizon.
    
    Args:
        days (int, optional): The number of days to look back in history. Defaults to 7.
        
    Returns:
        pd.DataFrame: A flattened pandas DataFrame containing columns for 'timestamp', 
                      'severity_level', 'location_name', and 'zone'. Ensure timestamp 
                      is parsed as datetime objects. Returns an empty DataFrame on failure.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/congestion/history?days={days}")
        response.raise_for_status()
        data = response.json()
        if not data:
            return pd.DataFrame()
            
        # Flatten the nested location dict
        flat_data = []
        for row in data:
            flat_row = row.copy()
            if 'locations' in flat_row:
                flat_row['location_name'] = flat_row['locations']['name']
                flat_row['zone'] = flat_row['locations']['zone']
                del flat_row['locations']
            flat_data.append(flat_row)
            
        df = pd.DataFrame(flat_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except:
        return pd.DataFrame()

def get_ai_insights(days_back=7):
    """
    Requests an AI-generated natural language summary of traffic conditions.
    
    Args:
        days_back (int, optional): Number of days of context to provide to the AI model. Defaults to 7.
        
    Returns:
        str: A Markdown-formatted string containing actionable insights and geographical 
             analysis provided by the Ollama Cloud model.
    """
    try:
        response = requests.post(f"{API_BASE_URL}/congestion/summarize", json={"days_back": days_back})
        response.raise_for_status()
        return response.json().get("summary", "No insight generated.")
    except Exception as e:
        return f"Error connecting to AI: {str(e)}"

# Custom CSS for Premium Glassmorphism Theme
custom_css = """
body {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
    color: #f8fafc;
    font-family: 'Inter', -apple-system, sans-serif;
    min-height: 100vh;
}
.bslib-sidebar-layout .sidebar {
    background: rgba(30, 41, 59, 0.7) !important;
    backdrop-filter: blur(15px);
    border-right: 1px solid rgba(255,255,255,0.05);
}
.card {
    background: rgba(30, 41, 59, 0.4) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    backdrop-filter: blur(12px);
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5) !important;
    border-radius: 16px !important;
    margin-bottom: 2.5rem;
    padding-bottom: 1.5rem;
}
.card-header {
    background: transparent !important;
    border-bottom: 1px solid rgba(255,255,255,0.05) !important;
    font-weight: 600;
    color: #38bdf8;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    font-size: 0.85rem;
}
.btn-primary {
    background: linear-gradient(135deg, #3b82f6 0%, #06b6d4 100%) !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(6, 182, 212, 0.3);
    transition: all 0.3s ease;
    border-radius: 8px;
    font-weight: 600;
}
.btn-primary:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(6, 182, 212, 0.5);
}
.irs-bar, .irs-bar-edge, .irs-single {
    background: #06b6d4 !important;
    border-color: #06b6d4 !important;
}
.irs-line {
    background: rgba(255,255,255,0.1) !important;
    border: none !important;
}
h2 {
    background: -webkit-linear-gradient(45deg, #e0f2fe, #0ea5e9);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
    letter-spacing: -1px;
    padding: 10px 0;
    margin: 0;
}
.navbar, .bslib-page-header, .bslib-page-title {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}
h4 {
    color: #f1f5f9;
    font-weight: 600;
}
.control-label {
    color: #94a3b8 !important;
    font-weight: 500;
}
.ai-box {
    margin-top: 1.5rem; 
    padding: 1.25rem; 
    background: rgba(0,0,0,0.25); 
    border-radius: 12px; 
    font-size: 0.95rem; 
    border-left: 4px solid #8b5cf6; 
    color: #e2e8f0;
    line-height: 1.6;
    box-shadow: inset 0 2px 10px rgba(0,0,0,0.2);
}
"""

# UI Layout
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h4("Control Panel"),
        ui.input_slider("days_back", "Time Horizon (Days):", min=1, max=365, value=30),
        ui.hr(style="border-color: rgba(255,255,255,0.05); margin: 2rem 0;"),
        ui.h4("AI Strategist"),
        ui.p("Generate macroscopic insights using Ollama Cloud intelligence.", style="font-size: 0.85rem; color: #94a3b8;"),
        ui.input_action_button("btn_insights", "✨ Generate Insights", class_="btn-primary w-100"),
        ui.output_ui("ai_summary_card")
    ),
    ui.head_content(ui.HTML(f"<style>{custom_css}</style>")),
    
    ui.p("Real-time monitoring and historical predictive analytics for metropolitan traffic flow.", style="color: #94a3b8; margin-bottom: 2rem;"),
    
    ui.layout_columns(
        ui.card(
            ui.card_header("Live Severity Index"),
            ui.output_plot("plot_current", fill=True)
        ),
        ui.card(
            ui.card_header("Historical Saturation Trends"),
            ui.output_plot("plot_history", fill=True)
        ),
        col_widths={"sm": (12, 12), "md": (12, 12), "lg": (6, 6)},
        height="450px",
        fill=False
    ),
    ui.div(style="height: 1.5rem;"),
    ui.card(
        ui.card_header("Macroscopic Congestion Heatmap (Hour vs Day)"),
        ui.output_plot("plot_heatmap", fill=True),
        height="400px"
    ),
    title=ui.h2("CityPulse Congestion Hub")
)

# Server Logic
def server(input, output, session):
    """
    The main server function for the Shiny application handling reactive logic and rendering.
    
    Args:
        input (Input): The object containing reactive values from UI inputs (e.g., input.days_back()).
        output (Output): The object used to define render outputs for the UI.
        session (Session): Information about the current user session connecting to the server.
    """
    
    insights_val = reactive.Value("Awaiting query command...")
    
    @reactive.Effect
    @reactive.event(input.btn_insights)
    def _():
        insights_val.set("Processing telemetry data...")
        summary = get_ai_insights(input.days_back())
        insights_val.set(summary)
        
    @output
    @render.ui
    def ai_summary_card():
        """
        Renders the dynamically generated AI insights inside a styled HTML div container.
        
        Returns:
            ui.TagList: Constructed HTML tags rendering the markdown string stored in `insights_val`.
        """
        return ui.div(
            ui.markdown(f"{insights_val()}"),
            class_="ai-box"
        )
        
    @output
    @render.plot
    def plot_current():
        """
        Renders the Live Severity Index bar chart.
        This function invalidates and re-evaluates itself every 1 second `invalidate_later(1)` 
        to simulate a high-frequency live dashboard update using dynamically injected jitter.
        
        Returns:
            matplotlib.figure.Figure: The rendered Matplotlib figure object.
        """
        reactive.invalidate_later(1) # Refresh every 1 second!
        
        df = fetch_current_congestion()
        if df.empty:
            return None
            
        import random
        df['live_variance'] = [random.uniform(-0.5, 0.5) for _ in range(len(df))]
        df['severity_level'] = (df['severity_level'] + df['live_variance']).clip(0, 5)
            
        import matplotlib.pyplot as plt
        
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_alpha(0.0)
        ax.patch.set_alpha(0.0)
        
        import matplotlib.cm as cm
        import matplotlib.colors as mcolors
        
        df_sorted = df.sort_values('severity_level', ascending=False)
        
        # Match 'mako' colormap logic: map severity (0 to 5)
        cmap = plt.get_cmap('mako')
        norm = mcolors.Normalize(vmin=0, vmax=5)
        
        colors = [cmap(norm(val)) for val in df_sorted['severity_level']]
        
        # Dynamic colored bars
        bars = ax.bar(df_sorted['name'], df_sorted['severity_level'], 
                      color=colors, alpha=0.9, edgecolor='white', linewidth=0.5)
        
        ax.set_ylim(0, 5)
        ax.set_ylabel("Severity Level", color="#94a3b8", fontsize=10)
        ax.tick_params(colors="#94a3b8", labelsize=9)
        
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        for spine in ['bottom', 'left']:
            ax.spines[spine].set_color('#334155')
            
        ax.yaxis.grid(True, color='#334155', linestyle='dashed')
        
        plt.xticks(rotation=45, ha='right')
        # Ensure deep bottom margin (bottom=0.25 leaves 25% of height for labels)
        plt.subplots_adjust(bottom=0.3, top=0.9, left=0.1, right=0.95)
        return fig
        
    @output
    @render.plot
    def plot_history():
        """
        Renders the Historical Saturation Trends line chart showing average daily severity.
        Reacts to changes in the `input.days_back()` UI slider.
        
        Returns:
            matplotlib.figure.Figure: The constructed Line chart with a categorical Set3 colormap.
        """
        df = fetch_historical_congestion(input.days_back())
        if df.empty:
            return None
            
        import matplotlib.pyplot as plt
        
        df['date'] = df['timestamp'].dt.date
        daily_avg = df.groupby(['date', 'location_name'])['severity_level'].mean().reset_index()
        
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(10, 5))
        fig.patch.set_alpha(0.0)
        ax.patch.set_alpha(0.0)
        import matplotlib.cm as cm
        import matplotlib.colors as mcolors
        
        # Use a bright categorical colormap for distinct lines
        cmap = plt.get_cmap('Set3')
        
        for idx, location in enumerate(daily_avg['location_name'].unique()):
            loc_data = daily_avg[daily_avg['location_name'] == location]
            
            c = cmap(idx % cmap.N)
            
            ax.plot(loc_data['date'], loc_data['severity_level'], 
                    marker='o', markersize=6, linewidth=2.5, 
                    color=c, label=location, alpha=0.9)
            
        ax.set_ylim(1, 5)
        ax.set_ylabel("Average Severity", color="#94a3b8", fontsize=10)
        ax.tick_params(colors="#94a3b8", labelsize=9)
        
        for spine in ['top', 'right']:
            ax.spines[spine].set_visible(False)
        for spine in ['bottom', 'left']:
            ax.spines[spine].set_color('#334155')
            
        ax.yaxis.grid(True, color='#334155', linestyle='dashed')
        
        plt.xticks(rotation=45, ha='right')
        plt.subplots_adjust(bottom=0.3, top=0.95, left=0.1, right=0.75)
        
        # Legend styling - balanced size
        legend = plt.legend(bbox_to_anchor=(1.02, 0.95), loc='upper left', 
                            frameon=True, facecolor='#0f172a', 
                            edgecolor='#334155', title="Zones",
                            fontsize=7, title_fontsize=8, 
                            markerscale=0.7, handlelength=1.5, labelspacing=0.4)
        plt.setp(legend.get_title(), color='#f8fafc')
        for text in legend.get_texts():
            text.set_color('#cbd5e1')
            
        return fig

    @output
    @render.plot
    def plot_heatmap():
        """
        Renders the Macroscopic Congestion Heatmap aggregating data by Day of Week vs Hour of Day.
        Uses Seaborn's heatmap functionality to plot congestion density.
        
        Returns:
            matplotlib.figure.Figure: The constructed Seaborn heatmap figure matching the 'mako' colormap.
        """
        import seaborn as sns
        df = fetch_historical_congestion(input.days_back())
        if df.empty:
            return None
            
        import matplotlib.pyplot as plt
        
        # Extract components for heatmap
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.day_name()
        
        # Provide chronological order for days of week
        days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        # Aggregate average severity
        heatmap_data = df.groupby(['day_of_week', 'hour'])['severity_level'].mean().unstack()
        heatmap_data = heatmap_data.reindex(days_order)
        
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(12, 5))
        fig.patch.set_alpha(0.0)
        ax.patch.set_alpha(0.0)
        
        # Seaborn heatmap
        sns.heatmap(heatmap_data, cmap='mako', ax=ax, 
                    linewidths=0.5, linecolor='#1e293b')
                    
        ax.set_xlabel("Hour of Day (24H)", color="#94a3b8", fontsize=10)
        ax.set_ylabel("Day of Week", color="#94a3b8", fontsize=10)
        ax.tick_params(colors="#94a3b8", labelsize=9)
        
        # Style colorbar ticks and text to match dark background
        cbar = ax.collections[0].colorbar
        cbar.ax.yaxis.set_tick_params(color='#94a3b8')
        cbar.outline.set_edgecolor('#334155')
        plt.setp(plt.getp(cbar.ax.axes, 'yticklabels'), color='#94a3b8')
        cbar.set_label('Average Severity', color='#94a3b8', size=10)
        
        plt.tight_layout()
        return fig

app = App(app_ui, server)
