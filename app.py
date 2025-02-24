import streamlit as st
import requests
import time

# Load API key securely from Streamlit secrets
FMP_API_KEY = st.secrets["FMP"]["api_key"]

# Define key support & resistance levels
RESISTANCE_LEVELS = [604.99, 606.44]  # Key resistance levels
SUPPORT_LEVELS = [592.88, 596.71]  # Key support levels
BUFFER = 1.5  # Price proximity buffer for alerts

# Function to fetch real-time SPY price from FMP API
def get_real_time_spy_price():
    url = f"https://financialmodelingprep.com/api/v3/quote/SPY?apikey={FMP_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if response.status_code == 200 and data:
        latest_price = data[0]["price"]
        return latest_price
    else:
        return None

# Function to check if SPY is near support or resistance
def check_spy_levels(price):
    messages = []

    for res in RESISTANCE_LEVELS:
        if abs(price - res) <= BUFFER:
            messages.append(f"⚠️ SPY is near **resistance** at **${res:.2f}**. Watch for a breakout!")

    for sup in SUPPORT_LEVELS:
        if abs(price - sup) <= BUFFER:
            messages.append(f"🟢 SPY is near **support** at **${sup:.2f}**. Possible bounce area.")

    return messages

# Streamlit App UI
st.title("📈 SPY Real-Time Price Tracker with Support & Resistance Alerts")
st.write("🔹 This app fetches **real-time SPY prices** and alerts when the price approaches key levels.")

# Real-time SPY price display
latest_price = get_real_time_spy_price()

if latest_price:
    st.metric(label="📊 Real-Time SPY Price", value=f"${latest_price:.2f}")

    # Check for alerts
    alerts = check_spy_levels(latest_price)

    if alerts:
        for alert in alerts:
            st.warning(alert)
    else:
        st.success("✅ SPY is trading normally within expected ranges.")

else:
    st.error("⚠️ Error fetching real-time price data. Please check API or internet connection.")

# Auto-refresh every 30 seconds
st.write("🔄 **Auto-refreshing every 30 seconds...**")
time.sleep(30)
st.experimental_rerun()
