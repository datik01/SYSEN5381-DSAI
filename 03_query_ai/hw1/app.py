import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

app_dir = Path(__file__).resolve().parent
load_dotenv(app_dir / ".env")
load_dotenv(app_dir.parent / ".env")

from api_query import get_aggs_bars
from ai_reporter import generate_report

# Timeframe: (multiplier, timespan) for Massive API
TIMEFRAMES = {
    "1m": (1, "minute"),
    "5m": (5, "minute"),
    "15m": (15, "minute"),
    "30m": (30, "minute"),
    "1H": (1, "hour"),
    "4H": (4, "hour"),
    "1D": (1, "day"),
    "1W": (1, "week"),
}

@st.cache_data(ttl=300)
def fetch_bars(ticker, multiplier, timespan, from_date, to_date, limit, sort="asc"):
    return get_aggs_bars(ticker, multiplier, timespan, from_date, to_date, limit=limit, sort=sort)


def bars_to_df(bars):
    if not bars:
        return pd.DataFrame()
    df = pd.DataFrame(bars)
    if "timestamp" in df.columns and df["timestamp"].notna().any():
        df["date"] = pd.to_datetime(df["timestamp"], unit="ms", utc=True).dt.tz_localize(None)
        df = df.sort_values("date").reset_index(drop=True)
    return df


# --- Page config ---
st.set_page_config(
    page_title="Market Analytics",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Sidebar ---
with st.sidebar:
    st.title("📈 Market Analytics")
    st.markdown("---")
    ticker = st.text_input("Ticker Symbol", value="AAPL").strip().upper() or "AAPL"
    tf_selected = st.selectbox("Timeframe", options=list(TIMEFRAMES.keys()), index=6)
    
    default_start = datetime.now().date() - timedelta(days=500)
    default_end = datetime.now().date()
    
    start_date = st.date_input("Start Date", value=default_start)
    end_date = st.date_input("End Date", value=default_end)
    st.markdown("---")
    st.caption("Powered by Massive API & Ollama")

# --- Chart title line ---
st.markdown(f"### {ticker}  •  {tf_selected}  •  {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

multiplier, timespan = TIMEFRAMES[tf_selected]

from_date = start_date.strftime("%Y-%m-%d")
to_date = end_date.strftime("%Y-%m-%d")
days_back = (end_date - start_date).days

# Intraday: request most recent bars (sort desc); modest window/limit to avoid 429
if timespan in ("minute", "hour"):
    if days_back > 21:
        from_dt = default_end - timedelta(days=21)
        from_date = from_dt.strftime("%Y-%m-%d")
        st.sidebar.warning("Intraday lookback capped at 21 days due to API limits.")
    limit = 500 if timespan == "minute" else 200
    sort = "desc"
else:
    limit = min(5000, days_back + 50)
    sort = "asc"

try:
    bars = fetch_bars(ticker, multiplier, timespan, from_date, to_date, limit, sort=sort)
except Exception as e:
    err_msg = str(e)
    if "429" in err_msg or "Max retries" in err_msg or "rate" in err_msg.lower():
        st.error("⚠️ Rate limited (429) — Wait 1–2 minutes and try again. Data is cached 5 min.")
    else:
        st.error(f"⚠️ API error: {err_msg}")
    st.stop()

if not bars:
    st.warning(f"No data for **{ticker}** ({from_date} → {to_date}). Try another symbol or range.")
    st.stop()

df = bars_to_df(bars)
if df.empty or "date" not in df.columns:
    st.warning("No time series data.")
    st.stop()

# --- Chart (main content) ---
inc = df["close"] >= df["open"]
colors = ["#26a69a" if i else "#ef5350" for i in inc]

fig = make_subplots(
    rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03,
    row_heights=[0.8, 0.2],
)
fig.add_trace(
    go.Candlestick(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name=ticker,
        increasing_line_color="#26a69a",
        decreasing_line_color="#ef5350",
    ),
    row=1, col=1,
)
if "volume" in df.columns:
    fig.add_trace(
        go.Bar(
            x=df["date"],
            y=df["volume"],
            marker_color=colors,
            showlegend=False,
            name="Volume"
        ),
        row=2, col=1,
    )

fig.update_layout(
    margin=dict(l=40, r=40, t=10, b=10),
    xaxis_rangeslider_visible=False,
    showlegend=False,
    hovermode="x unified",
    height=600,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="gray"
)
fig.update_xaxes(showgrid=True, gridcolor="rgba(128,128,128,0.2)")
fig.update_yaxes(showgrid=True, gridcolor="rgba(128,128,128,0.2)")

st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": True, "displaylogo": False})

# --- Metrics Strip ---
last = df.iloc[-1]
first = df.iloc[0]

period_open = first.get("open", 0)
period_high = df["high"].max() if "high" in df.columns else 0
period_low = df["low"].min() if "low" in df.columns else 0
period_close = last.get("close", 0)
period_volume = df["volume"].sum() if "volume" in df.columns else 0

chg = (period_close - period_open) / period_open * 100 if period_open else 0
chg_val = period_close - period_open

cols = st.columns(6)
cols[0].metric("Open", f"{period_open:.2f}")
cols[1].metric("High", f"{period_high:.2f}")
cols[2].metric("Low", f"{period_low:.2f}")
cols[3].metric("Close", f"{period_close:.2f}")
cols[4].metric("Volume", f"{period_volume:,.0f}")
cols[5].metric("Change (%)", f"{chg:+.2f}%", delta=f"{chg_val:+.2f}")

st.markdown("---")

# --- Tabs: Data table & AI Summary ---
tab1, tab2 = st.tabs(["📝 AI Report", "🗃️ Data Table"])

with tab1:
    report_key = f"ai_report_{ticker}"
    if report_key not in st.session_state:
        st.session_state[report_key] = None
        
    col_btn, col_content = st.columns([1, 3])
    with col_btn:
        if st.button("Generate Report", type="primary", use_container_width=True):
            with st.spinner("Analyzing..."):
                try:
                    # Calculate Technical Indicators
                    df_ta = df.copy()
                    df_ta["SMA_20"] = df_ta["close"].rolling(window=20).mean().round(2)
                    df_ta["EMA_9"] = df_ta["close"].ewm(span=9, adjust=False).mean().round(2)
                    
                    # Calculate RSI 14
                    delta = df_ta["close"].diff()
                    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                    rs = gain / loss
                    df_ta["RSI_14"] = (100 - (100 / (1 + rs))).round(2)
                    
                    # Ensure we have enough data to show the indicators, then take the last 15 rows
                    sample = df_ta[["date", "open", "high", "low", "close", "volume", "SMA_20", "EMA_9", "RSI_14"]].tail(15).copy()
                    
                    # Convert date to string for the AI so it doesn't get confused
                    sample["date"] = sample["date"].dt.strftime("%Y-%m-%d")
                    sample["ticker"] = ticker
                    
                    # Clean up NaNs from the rolling calculations
                    sample = sample.fillna("N/A")
                    
                    report = generate_report(
                        sample.to_dict("records"),
                        tickers_label=f"{ticker} ({tf_selected} timeframe)"
                    )
                    st.session_state[report_key] = report
                except Exception as e:
                    st.error(f"Error generating report: {e}")
                    
    with col_content:
        if st.session_state[report_key]:
            st.info(st.session_state[report_key])
        else:
            st.caption("Click 'Generate Report' to get an AI summary of the visible data.")

with tab2:
    st.dataframe(
        df[["date", "open", "high", "low", "close", "volume"]].sort_values("date", ascending=False),
        use_container_width=True,
        hide_index=True
    )
