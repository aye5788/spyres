import streamlit as st
import requests
import numpy as np
import pandas as pd

# FMP API Key from Streamlit Secrets
FMP_API_KEY = st.secrets["FMP"]["api_key"]

# Define key support & resistance levels
RESISTANCE_LEVELS = [604.99, 606.44]  # Resistance Zones
SUPPORT_LEVELS = [592.88, 596.71]  # Support Zones
BUFFER = 1.5  # Buffer for alerts

# Function to fetch real-time SPY price
def get_real_time_spy_price():
    url = f"https://financialmodelingprep.com/api/v3/quote/SPY?apikey={FMP_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if response.status_code == 200 and data:
        return data[0]["price"]
    return None

# Function to fetch historical price data (for probability calculation)
def get_historical_data():
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/SPY?apikey={FMP_API_KEY}&timeseries=30"
    response = requests.get(url)
    data = response.json()
    
    if "historical" in data:
        df = pd.DataFrame(data["historical"])
        df = df[["date", "close"]].sort_values("date")  # Keep only date & close price
        df["returns"] = df["close"].pct_change()  # Daily returns
        return df.dropna()
    return None

# Function to estimate probability of breaking key levels
def calculate_break_probability(current_price, df):
    if df is None or df.empty:
        return "Data unavailable"

    volatility = df["returns"].std()  # Historical volatility
    price_range = max(df["close"]) - min(df["close"])  # Range of prices in 30 days

    # Estimate probability using normalized proximity & volatility
    probabilities = {}
    for level in SUPPORT_LEVELS + RESISTANCE_LEVELS:
        distance = abs(current_price - level) / price_range
        prob = min(1, (1 - distance) * (volatility * 10))  # Scaling factor
        probabilities[level] = round(prob * 100, 2)  # Convert to percentage

    return probabilities

# Streamlit App UI
st.title("📈 SPY Real-Time Price Tracker with Probabilities")
st.write("🔹 This app fetches **real-time SPY prices**, key levels, and estimated probabilities of breaking support/resistance.")

# Get real-time price
spy_price = get_real_time_spy_price()

if spy_price:
    st.metric(label="📊 Real-Time SPY Price", value=f"${spy_price:.2f}")

    # Get historical data for probability estimation
    df = get_historical_data()
    probabilities = calculate_break_probability(spy_price, df)

    # Display upcoming key levels & probabilities
    st.subheader("📍 Nearest Key Levels & Probabilities")

    for level in sorted(SUPPORT_LEVELS + RESISTANCE_LEVELS):
        if level > spy_price:
            st.write(f"🔴 **Resistance at ${level:.2f}** → Probability of Breakout: **{probabilities[level]}%**")
        else:
            st.write(f"🟢 **Support at ${level:.2f}** → Probability of Breakdown: **{probabilities[level]}%**")

    # Highlight potential trade signals
    if any(prob > 70 for prob in probabilities.values()):
        st.warning("⚠️ High probability of a breakout or breakdown detected!")
    else:
        st.success("✅ No extreme risk detected.")

else:
    st.error("⚠️ Error fetching real-time SPY price.")

# Auto-refresh every 30 seconds
st.write("🔄 **Auto-refreshing every 30 seconds...**")
st.experimental_rerun()

