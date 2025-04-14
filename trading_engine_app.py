import streamlit as st
import pandas as pd
import sys
import requests
from datetime import date
from pathlib import Path
import altair as alt

project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

st.set_page_config(
    page_title="Trading Engine Backtester",
    layout="wide",
    initial_sidebar_state="expanded"
)

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Custom styling
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
body {
    font-family: 'Inter', sans-serif;
    background: #111827;
    color: #FFFFFF;
}
[data-testid="stSidebar"] {
    border-right: 1px solid #4B5563;
    background-color: #1F2937 !important;
}
.css-1cpxqw2, .css-1d391kg {
    background-color: #374151 !important;
    color: #FFFFFF !important;
    border-radius: 4px;
    padding: 0.5rem 0.75rem;
}
.stButton button {
    background-color: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 4px;
    padding: 0.5rem 1rem;
    font-weight: 600;
}
.stButton button:hover {
    background-color: #1D4ED8;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style="margin-bottom: 2rem;">
    <h1 style="font-size: 2.5rem; font-weight: 800;">Trading Engine</h1>
    <p style="color: #9CA3AF; font-size: 1.1rem; margin-top: 0.5rem;">
        Select your stock and timeframe in the sidebar, then adjust the technical indicator settings below to simulate your potential trading returns.
    </p>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("Data Parameters")
symbol = st.sidebar.selectbox("Stock Symbol", options=["AAPL", "TSLA", "MSFT", "AMZN", "NVDA", "NFLX", "V", "GOOGL"])
period = st.sidebar.selectbox("Period", options=["None", "1d", "5d", "1mo", "3mo", "6mo", "1y"], index=0)
interval = st.sidebar.selectbox("Interval", options=["1d", "1h", "30m", "15m", "5m"])

if period == "None":
    start_date = st.sidebar.date_input("Start Date", value=date(2025, 1, 1))
    end_date = st.sidebar.date_input("End Date", value=date(2025, 1, 31))
else:
    start_date = None
    end_date = None

# Move Preview Price Chart button here
preview_price = st.sidebar.button("Preview Price Chart")

if preview_price:
    try:
        from data.yf_data import stock_history

        start_str = str(start_date) if start_date else None
        end_str = str(end_date) if end_date else None

        with st.spinner("Fetching data..."):
            data = stock_history(
                symbol,
                period if period != "None" else None,
                interval,
                start_str,
                end_str
            )

        if isinstance(data, list):
            data = pd.DataFrame([{
                "Date": d.date,
                "Open": d.open,
                "High": d.high,
                "Low": d.low,
                "Close": d.close,
                "Volume": d.volume
            } for d in data])

        if data.empty:
            st.warning("No data returned. Please adjust your parameters.")
        else:
            st.success("Data fetched successfully!")
            st.subheader(f"{symbol} Price Preview")
            price_chart = alt.Chart(data).mark_line().encode(
                x="Date:T",
                y=alt.Y("Close:Q", scale=alt.Scale(domain=[data["Close"].min() * 0.995, data["Close"].max() * 1.005])),
                tooltip=["Date:T", "Close:Q"]
            ).properties(
                width="container",
                height=300
            ).interactive()

            st.altair_chart(price_chart, use_container_width=True)
    except Exception as e:
        st.error(f"Error fetching preview data: {e}")

with st.container():
    st.subheader("Strategy Configuration")

    # SMA
    use_sma = st.checkbox("SMA", value=True)
    if use_sma:
        with st.expander("Simple Moving Average Settings", expanded=True):
            sma_period = st.slider("SMA Period", 5, 100, 20)
            sma_source = st.selectbox("SMA Source", ["Close", "Open", "High", "Low"])

    # RSI
    use_rsi = st.checkbox("RSI", value=False)
    if use_rsi:
        with st.expander("Relative Strength Index Settings", expanded=True):
            rsi_period = st.slider("RSI Period", 5, 50, 14)
            rsi_overbought = st.slider("Overbought Level", 60, 90, 70)
            rsi_oversold = st.slider("Oversold Level", 10, 40, 30)

    # MACD
    use_macd = st.checkbox("MACD", value=False)
    if use_macd:
        with st.expander("MACD Settings", expanded=True):
            macd_fast = st.slider("MACD Fast EMA", 5, 20, 12)
            macd_slow = st.slider("MACD Slow EMA", 10, 50, 26)
            macd_signal = st.slider("MACD Signal EMA", 5, 20, 9)

    # Bollinger Bands
    use_bbands = st.checkbox("Bollinger Bands", value=False)
    if use_bbands:
        with st.expander("Bollinger Bands Settings", expanded=True):
            bbands_period = st.slider("BBands Period", 5, 100, 20)
            bbands_stddev = st.slider("BBands Std Dev", 1.0, 5.0, 2.0, step=0.1)

    with st.expander("Trade Settings", expanded=True):
        take_profit = st.slider("Take Profit (%)", 1, 100, 10)
        stop_loss = st.slider("Stop Loss (%)", 1, 100, 5)

    trade_logic = st.radio(
        "Trade Logic",
        options=["All", "Any"],
        index=0,
        help="Select whether all enabled indicators must agree (All) or if any indicator can signal a trade (Any)."
    )

    st.markdown("---")

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    run_button = st.button("Run Engine", use_container_width=True)

if run_button:
    try:
        start_str = str(start_date) if start_date else None
        end_str = str(end_date) if end_date else None

        with st.spinner("Fetching data..."):
            data = stock_history(
                symbol,
                period if period != "None" else None,
                interval,
                start_str,
                end_str
            )

        if isinstance(data, list):
            data = pd.DataFrame([{
                "Date": d.date,
                "Open": d.open,
                "High": d.high,
                "Low": d.low,
                "Close": d.close,
                "Volume": d.volume
            } for d in data])

        if data.empty:
            st.warning("No data returned. Please adjust your parameters.")
        else:
            st.success("Data fetched successfully!")

            strategy_settings = {
                "sma": {
                    "enabled": use_sma,
                    "period": sma_period if use_sma else None,
                    "source": sma_source.lower() if use_sma else None
                },
                "rsi": {
                    "enabled": use_rsi,
                    "period": rsi_period if use_rsi else None,
                    "overbought": rsi_overbought if use_rsi else None,
                    "oversold": rsi_oversold if use_rsi else None
                },
                "macd": {
                    "enabled": use_macd,
                    "fast": macd_fast if use_macd else None,
                    "slow": macd_slow if use_macd else None,
                    "signal": macd_signal if use_macd else None
                },
                "bbands": {
                    "enabled": use_bbands,
                    "period": bbands_period if use_bbands else None,
                    "std_dev": bbands_stddev if use_bbands else None
                }
            }

            payload = {
                "symbol": symbol,
                "interval": interval,
                "start_date": start_str,
                "end_date": end_str,
                "price_data": data.copy().assign(Date=lambda df: df["Date"].astype(str)).to_dict(orient="records"),
                "indicators": strategy_settings,
                "trade_logic": trade_logic.lower(),
                "take_profit": take_profit,
                "stop_loss": stop_loss,
            }

            with st.spinner("Running strategy analysis..."):
                # Send to Axum endpoint
                response = requests.post("http://localhost:8001/strategy", json=payload)
                results = response.json()

            st.metric("Strategy ROI", f"{results['roi'] * 100:.2f}%")
            chart_df = pd.DataFrame(results["chart_data"])
            chart_df["date"] = pd.to_datetime(chart_df["date"])
            chart_df = chart_df.set_index("date")

            st.subheader("Backtest Results")
            st.line_chart(chart_df[["close"] +
                (["sma"] if use_sma and "sma" in chart_df.columns else []) +
                (["macd", "macd_signal"] if use_macd and "macd" in chart_df.columns else []) +
                (["bb_upper", "bb_lower"] if use_bbands and "bb_upper" in chart_df.columns else [])
            ])
    except Exception as e:
        st.error(f"Error running strategy: {e}")