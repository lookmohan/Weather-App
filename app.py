import streamlit as st
import requests
import json
from datetime import datetime
from fpdf import FPDF
import matplotlib.pyplot as plt
import os
from streamlit_lottie import st_lottie
import pandas as pd

# Initialize session state
if 'get_weather' not in st.session_state:
    st.session_state.get_weather = False

# Load API keys safely
try:
    weather_api_key = st.secrets["WAK"]
    huggingface_api_key = st.secrets["HAK"]
except Exception as e:
    st.error(f"Error loading API keys: {str(e)}")
    weather_api_key = ""
    huggingface_api_key = ""

# Load Lottie animations with retry logic
def load_lottieurl(url, max_retries=3):
    for _ in range(max_retries):
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception:
            continue
    return None

# Preload animations
lottie_rainy = load_lottieurl("https://assets8.lottiefiles.com/packages/lf20_kcsr6fcp.json")
lottie_sunny = load_lottieurl("https://assets4.lottiefiles.com/packages/lf20_pmvvvcdb.json")
lottie_cloudy = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_1pxqjqps.json")
lottie_weather = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_5tkzkblw.json")

# Functions
def get_weather_data(city, api_key):
    url = f"http://api.openweathermap.org/data/2.5/weather?appid={api_key}&q={city}"
    return requests.get(url).json()

def get_weekly_forecast(api_key, lat, lon):
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}"
    return requests.get(url).json()

def generate_forecast_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Weekly Weather Forecast", ln=True, align='C')
    pdf.ln()

    seen_dates = set()
    for item in data['list']:
        date = datetime.fromtimestamp(item['dt']).strftime('%A, %B %d')
        if date not in seen_dates:
            seen_dates.add(date)
            min_temp = item['main']['temp_min'] - 273.15
            max_temp = item['main']['temp_max'] - 273.15
            desc = item['weather'][0]['description']
            pdf.cell(0, 10, txt=f"{date}: {desc.title()}, {min_temp:.1f}°C to {max_temp:.1f}°C", ln=True)

    path = "forecast.pdf"
    pdf.output(path)
    return path

def display_forecast_chart(data):
    dates = []
    temps = []
    for item in data['list']:
        dt = datetime.fromtimestamp(item['dt']).strftime('%d %b %H:%M')
        temp = item['main']['temp'] - 273.15
        dates.append(dt)
        temps.append(temp)

    plt.figure(figsize=(12, 6))
    plt.plot(dates, temps, marker='o', color='#4CAF50')
    plt.xticks(rotation=45)
    plt.title("5-Day Temperature Forecast")
    plt.tight_layout()
    plt.grid(True)
    plt.savefig("forecast_chart.png", transparent=True)
    st.image("forecast_chart.png")

def generate_weather_description(data, api_key):
    try:
        temp = data['main']['temp'] - 273.15
        desc = data['weather'][0]['description']
        prompt = f"The current weather is {desc} at {temp:.1f}°C. Explain this simply."
        response = requests.post(
            "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={"inputs": prompt, "parameters": {"max_new_tokens": 60}}
        )
        result = response.json()
        if isinstance(result, list) and 'generated_text' in result[0]:
            return result[0]['generated_text'].strip()
        return "Weather summary unavailable."
    except Exception:
        return "AI summary failed."

def get_weather_animation(condition):
    if not condition: return lottie_weather
    cond = condition.lower()
    if 'rain' in cond: return lottie_rainy
    if 'clear' in cond: return lottie_sunny
    if 'cloud' in cond: return lottie_cloudy
    return lottie_weather

# Main Streamlit App
def main():
    st.set_page_config(page_title="Weather Forecast with AI", page_icon="🌦", layout="centered")

    # Sidebar
    with st.sidebar:
        try:
            generic_animation = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_5tkzkblw.json")
            if generic_animation:
                st_lottie(generic_animation, height=150, key="sidebar")
        except Exception:
            st.warning("Could not load sidebar animation.")

        st.title("🌦 Weather Forecast")
        city = st.text_input("Enter city name", "London")
        if st.button("Get Weather"):
            st.session_state.get_weather = True

    # Main logic
    if st.session_state.get_weather and city:
        st.title(f"Weather in {city}")
        with st.spinner("Fetching weather data..."):
            weather = get_weather_data(city, weather_api_key)
            if weather.get("cod") != 200:
                st.error(weather.get("message", "Could not fetch weather."))
                return

            anim = get_weather_animation(weather['weather'][0]['main'])
            col1, col2 = st.columns([1, 2])
            with col1:
                if anim: st_lottie(anim, height=200)
            with col2:
                st.subheader("Current Weather")
                st.write(weather['weather'][0]['description'].title())

            st.metric("Temperature", f"{weather['main']['temp'] - 273.15:.1f} °C")
            st.metric("Humidity", f"{weather['main']['humidity']}%")
            st.metric("Pressure", f"{weather['main']['pressure']} hPa")
            st.metric("Wind Speed", f"{weather['wind']['speed']} m/s")

            try:
                lat, lon = weather['coord']['lat'], weather['coord']['lon']
                forecast = get_weekly_forecast(weather_api_key, lat, lon)
                if forecast.get("cod") == "200":
                    st.subheader("Forecast Chart")
                    display_forecast_chart(forecast)

                    st.subheader("AI Summary")
                    st.write(generate_weather_description(weather, huggingface_api_key))

                    pdf_path = generate_forecast_pdf(forecast)
                    with open(pdf_path, "rb") as f:
                        st.download_button("📄 Download Forecast PDF", f, file_name="forecast.pdf")
            except Exception as e:
                st.error(f"Forecast error: {str(e)}")

if __name__ == "__main__":
    main()
