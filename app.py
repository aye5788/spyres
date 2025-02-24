
import streamlit as st
import requests
import numpy as np
import pandas as pd
from scipy.stats import beta  # Bayesian beta distribution
from textblob import TextBlob  # NLP for sentiment analysis

# Set wide layout for better readability
st.set_page_config(layout="wide")

# FMP API Key from Streamlit Secrets
FMP_API_KEY = st.secrets["FMP"]["api_key"]

# Define key support & resistance levels
RESISTANCE_LEVELS = [604.99, 606.44]  
SUPPORT_LEVELS = [592.88, 596.71]  
BUFFER = 1.5  

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
        df["returns"] = df["close"].pct_change()  
        return df.dropna()
    return None

# Function to fetch real-time news for SPY
def get_spy_news():
    url = f"https://financialmodelingprep.com/api/v3/stock_news?tickers=SPY&limit=5&apikey={FMP_API_KEY}"
    response = requests.get(url)
    data = response.json()

    news_headlines = []
    sentiment_scores = []
    
    if response.status_code == 200 and data:
        for article in data[:5]:  # Get top 5 latest news articles
            headline = article["title"]
            news_headlines.append(headline)
            
            # Perform sentiment analysis
            sentiment = TextBlob(headline).sentiment.polarity  # Score between -1 (negative) to 1 (positive)
            sentiment_scores.append(sentiment)
    
    avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0
    return news_headlines, avg_sentiment

# Function to estimate probability of breaking key levels using Bayesian inference + News Sentiment
def calculate_bayesian_probabilities(current_price, current_volume, df, sentiment_score):
    if df is None or df.empty:
        return "Data unavailable"

    volatility = df["returns"].std()  
    avg_volume = df["volume"].mean()  

    probabilities = {}

    for level in SUPPORT_LEVELS + RESISTANCE_LEVELS:
        distance = abs(current_price - level) / (max(df["close"]) - min(df["close"]))  
        recent_momentum = df["returns"].rolling(5).mean().iloc[-1]  
        volume_factor = current_volume / avg_volume  

        # Bayesian probability estimation: Prior based on distance, adjusted by momentum & volume
        alpha = 1 + (1 - distance) * 5  
        beta_val = 1 + max(0, -recent_momentum * 10) + (1 / max(volume_factor, 1))  

        prob = beta(alpha, beta_val).mean()  

        # Adjust probability based on news sentiment (Positive sentiment increases breakout chance, Negative increases breakdown)
        if level in RESISTANCE_LEVELS:
            prob += sentiment_score * 5  # Boost breakout probability for positive news
        else:
            prob -= sentiment_score * 5  # Increase breakdown probability for negative news

        probabilities[level] = round(max(0, min(prob * 100, 100)), 2)  

    return probabilities

# Streamlit App UI
st.markdown("<h1 style='text-align: center;'>📈 Bayesian SPY Tracker with News Sentiment</h1>", unsafe_allow_html=True)

# Get real-time price, volume, and news sentiment
spy_price, spy_volume = get_real_time_spy_data()
news_headlines, sentiment_score = get_spy_news()

if spy_price and spy_volume:
    # Use Streamlit columns to organize layout
    col1, col2 = st.columns([1, 2])

    with col1:
        st.metric(label="📊 SPY Price", value=f"${spy_price:.2f}")
        st.metric(label="📊 Volume", value=f"{spy_volume:,}")
        st.metric(label="📰 News Sentiment", value=f"{sentiment_score:.2f}")

    with col2:
        df = get_historical_data()
        probabilities = calculate_bayesian_probabilities(spy_price, spy_volume, df, sentiment_score)

        st.markdown("<h3 style='text-align: center;'>📍 Bayesian Key Levels & Probabilities</h3>", unsafe_allow_html=True)

        # Organize Key Levels into Two Columns
        col_support, col_resistance = st.columns(2)

        with col_support:
            st.markdown("### 🟢 Support Levels")
            for level in sorted(SUPPORT_LEVELS):
                st.write(f"**Support at ${level:.2f}** → Breakdown Probability: **{probabilities[level]}%**")

        with col_resistance:
            st.markdown("### 🔴 Resistance Levels")
            for level in sorted(RESISTANCE_LEVELS):
                st.write(f"**Resistance at ${level:.2f}** → Breakout Probability: **{probabilities[level]}%**")

        # Find the highest probability event
        highest_prob_level = max(probabilities, key=probabilities.get)
        highest_prob_value = probabilities[highest_prob_level]

        if highest_prob_value > 70:
            if highest_prob_level in RESISTANCE_LEVELS:
                st.warning(f"⚠️ **{highest_prob_value:.2f}% chance of breaking RESISTANCE at ${highest_prob_level:.2f}.**")
                st.write("📈 **Bullish momentum detected. Watch for a breakout!**")
            else:
                st.warning(f"⚠️ **{highest_prob_value:.2f}% chance of breaking SUPPORT at ${highest_prob_level:.2f}.**")
                st.write("📉 **Downside pressure detected. Watch for a breakdown!**")
        else:
            st.success("✅ No extreme risk detected.")

    # Display recent news headlines
    st.markdown("### 📰 Latest SPY News & Sentiment")
    for headline in news_headlines:
        st.write(f"- {headline}")

else:
    st.error("⚠️ Error fetching real-time SPY data.")

# Auto-refresh settings
st.markdown("---")
if st.button("🔄 Refresh Now"):
    st.rerun()
