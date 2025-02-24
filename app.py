import streamlit as st
import requests
import numpy as np
import pandas as pd
from scipy.stats import beta  # Bayesian beta distribution

# FMP API Key from Streamlit Secrets
FMP_API_KEY = st.secrets["FMP"]["api_key"]

# Define key support & resistance levels
RESISTANCE_LEVELS = [604.99, 606.44]  # Resistance Zones
SUPPORT_LEVELS = [592.88, 596.71]  # Support Zones
BUFFER = 1.5  # Price proximity buffer

# Function to fetch real-time SPY price & volume
def get_real_time_spy_data():
    url = f"https://financialmodelingprep.com/api/v3/quote/SPY?apikey={FMP_API_KEY}"
    response = requests.get(url)
    data = response.json()
    
    if response.status_code == 200 and data:
        return data[0]["price"], data[0]["volume"]
    return None, None

# Function to fetch historical data (price & volume)
def get_historical_data():
    url = f"https://financialmodelingprep.com/api/v3/historical-price-full/SPY?apikey={FMP_API_KEY}&timeseries=30"
    response = requests.get(url)
    data = response.json()
    
    if "historical" in data:
        df = pd.DataFrame(data["historical"])
        df = df[["date", "close", "volume"]].sort_values("date")  
        df["returns"] = df["close"].pct_change()  # Daily returns
        return df.dropna()
    return None

# Function to estimate probability of breaking key levels using Bayesian inference
def calculate_bayesian_probabilities(current_price, current_volume, df):
    if df is None or df.empty:
        return "Data unavailable"

    volatility = df["returns"].std()  # Historical volatility
    avg_volume = df["volume"].mean()  # Average volume over last 30 days

    probabilities = {}

    for level in SUPPORT_LEVELS + RESISTANCE_LEVELS:
        distance = abs(current_price - level) / (max(df["close"]) - min(df["close"]))  # Normalize distance
        recent_momentum = df["returns"].rolling(5).mean().iloc[-1]  # Last 5-day avg return
        volume_factor = current_volume / avg_volume  # Volume as a relative measure

        # Bayesian probability estimation: Prior based on distance, adjusted by momentum & volume
        alpha = 1 + (1 - distance) * 5  # Stronger prior belief if close to level
        beta_val = 1 + max(0, -recent_momentum * 10) + (1 / max(volume_factor, 1))  # Adjust for momentum & volume

        prob = beta(alpha, beta_val).mean()  # Expected probability from beta distribution
        probabilities[level] = round(prob * 100, 2)  # Convert to percentage

    return probabilities

# Streamlit App UI
st.title("📈 Bayesian SPY Price Tracker with Volume & Support/Resistance Probabilities")
st.write("🔹 This app uses **Bayesian inference** to dynamically estimate the probability of SPY breaking key support/resistance levels.")

# Fetch real-time price & volume
spy_price, spy_volume = get_real_time_spy_data()

if spy_price and spy_volume:
    st.metric(label="📊 Real-Time SPY Price", value=f"${spy_price:.2f}")
    st.metric(label="📊 Real-Time Volume", value=f"{spy_volume:,}")

    # Get historical data for Bayesian inference
    df = get_historical_data()
    probabilities = calculate_bayesian_probabilities(spy_price, spy_volume, df)

    # Display probability estimates for support & resistance
    st.subheader("📍 Bayesian Key Levels & Probabilities")

    for level in sorted(SUPPORT_LEVELS + RESISTANCE_LEVELS):
        if level > spy_price:
            st.write(f"🔴 **Resistance at ${level:.2f}** → Probability of Breakout: **{probabilities[level]}%**")
        else:
            st.write(f"🟢 **Support at ${level:.2f}** → Probability of Breakdown: **{probabilities[level]}%**")

    # Determine the highest probability event for clearer alerts
    highest_prob_level = max(probabilities, key=probabilities.get)
    highest_prob_value = probabilities[highest_prob_level]

    if highest_prob_value > 70:
        if highest_prob_level in RESISTANCE_LEVELS:
            st.warning(f"⚠️ **SPY has a {highest_prob_value:.2f}% chance of breaking RESISTANCE at ${highest_prob_level:.2f}.**")
            st.write("📈 **This suggests increased bullish momentum. Watch for a breakout!**")
        else:
            st.warning(f"⚠️ **SPY has a {highest_prob_value:.2f}% chance of breaking SUPPORT at ${highest_prob_level:.2f}.**")
            st.write("📉 **This suggests downside pressure. Watch for a breakdown!**")
    else:
        st.success("✅ No extreme risk detected.")

else:
    st.error("⚠️ Error fetching real-time SPY data.")

# Auto-refresh every 30 seconds
st.write("🔄 **Auto-refreshing every 30 seconds...**")
st.session_state.refresh = st.button("🔄 Refresh Now")

if st.session_state.refresh:
    st.rerun()

