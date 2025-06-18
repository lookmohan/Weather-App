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
    st.session_state['get_weather'] = False

# Load API keys with error handling
try:
    weather_api_key = st.secrets["WAK"]
    huggingface_api_key = st.secrets["HAK"]
except Exception as e:
    st.error(f"Error loading API keys: {str(e)}")
    st.stop()

# Safe Lottie animation loader
def load_lottieurl(url):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None

# Load Lottie animations with fallbacks
lottie_weather = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_5tkzkblw.json") or {}
lottie_sunny = load_lottieurl("https://assets4.lottiefiles.com/packages/lf20_pmvvvcdb.json") or lottie_weather
lottie_rainy = load_lottieurl("https://assets8.lottiefiles.com/packages/lf20_kcsr6fcp.json") or lottie_weather
lottie_cloudy = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_1pxqjqps.json") or lottie_weather

# Weather data functions
def get_weather_data(city, weather_api_key):
    try:
        base_url = "http://api.openweathermap.org/data/2.5/weather?"
        complete_url = f"{base_url}appid={weather_api_key}&q={city}"
        response = requests.get(complete_url, timeout=10)
        return response.json()
    except Exception:
        return {"cod": "500", "message": "Connection error"}

def get_weekly_forecast(weather_api_key, lat, lon):
    try:
        forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={weather_api_key}"
        response = requests.get(forecast_url, timeout=10)
        return response.json()
    except Exception:
        return {"cod": "500", "message": "Connection error"}

def display_forecast_chart(data):
    try:
        dates = []
        temps = []
        for item in data['list']:
            dt = datetime.fromtimestamp(item['dt']).strftime('%d %b %H:%M')
            temp = item['main']['temp'] - 273.15
            dates.append(dt)
            temps.append(temp)

        plt.figure(figsize=(12, 6))
        plt.plot(dates, temps, marker='o', color='#4CAF50', linewidth=2, markersize=8)
        plt.xticks(rotation=45)
        plt.title("5-Day Temperature Forecast", fontsize=14, pad=20)
        plt.xlabel("DateTime", fontsize=12)
        plt.ylabel("Temperature (°C)", fontsize=12)
        plt.tight_layout()
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.savefig("forecast_chart.png", transparent=True)
        st.image("forecast_chart.png")
    except Exception as e:
        st.error(f"Chart generation error: {str(e)}")

def generate_weather_description(data, huggingface_api_key):
    try:
        temperature = data['main']['temp'] - 273.15
        description = data['weather'][0]['description']
        prompt = f"The current weather in your city is {description} with a temperature of {temperature:.1f}°C. Explain this in a simple way."

        api_url = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
        headers = {
            "Authorization": f"Bearer {huggingface_api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": 60}
        }

        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', '').strip()
        return "Weather summary unavailable right now"
    except Exception:
        return "Weather description service unavailable"

def get_weather_animation(weather_condition):
    if not weather_condition:
        return lottie_weather
    weather_condition = weather_condition.lower()
    if 'rain' in weather_condition:
        return lottie_rainy
    elif 'clear' in weather_condition:
        return lottie_sunny
    elif 'cloud' in weather_condition:
        return lottie_cloudy
    return lottie_weather

def generate_forecast_pdf(forecast_data, city, current_weather):
    try:
        pdf = FPDF()
        pdf.add_page()

        pdf.set_font("Arial", 'B', 16)
        pdf.cell(200, 10, txt=f"Weather Forecast Report for {city}", ln=True, align='C')
        pdf.ln(10)

        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Current Weather", ln=True)
        pdf.set_font("Arial", '', 12)

        current_temp = current_weather['main']['temp'] - 273.15
        weather_desc = current_weather['weather'][0]['description'].title()

        pdf.multi_cell(0, 10, txt=(
            f"Temperature: {current_temp:.1f}°C\n"
            f"Conditions: {weather_desc}\n"
            f"Humidity: {current_weather['main']['humidity']}%\n"
            f"Pressure: {current_weather['main']['pressure']} hPa\n"
            f"Wind Speed: {current_weather['wind']['speed']} m/s"
        ))

        if os.path.exists("forecast_chart.png"):
            pdf.ln(10)
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(200, 10, txt="5-Day Forecast", ln=True)
            pdf.image("forecast_chart.png", x=10, w=190)

        pdf.ln(10)
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="Daily Forecast", ln=True)

        daily_data = {}
        for item in forecast_data['list']:
            date = datetime.fromtimestamp(item['dt']).strftime('%A, %B %d')
            if date not in daily_data:
                daily_data[date] = []
            daily_data[date].append(item)

        for date, items in daily_data.items():
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, txt=date, ln=True)

            temps = [item['main']['temp'] - 273.15 for item in items]
            min_temp, max_temp = min(temps), max(temps)

            pdf.set_font("Arial", '', 10)
            pdf.cell(0, 8, txt=f"High: {max_temp:.1f}°C, Low: {min_temp:.1f}°C", ln=True)

            conditions = list(set(item['weather'][0]['description'].title() for item in items))
            pdf.cell(0, 8, txt=f"Conditions: {', '.join(conditions)}", ln=True)
            pdf.ln(5)

        pdf.ln(10)
        pdf.set_font("Arial", 'I', 8)
        pdf.cell(0, 10, txt=f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')

        path = f"weather_forecast_{city}.pdf"
        pdf.output(path)
        return path
    except Exception as e:
        st.error(f"PDF generation error: {str(e)}")
        return None


# Streamlit app
def main():
    st.set_page_config(page_title="Weather Forecast with AI", page_icon="🌦", layout="centered")

    with st.sidebar:
        st.markdown("## 🌍 Weather Forecast")
        city = st.text_input("Enter city name", "London")
        if st.button("Get Weather"):
            st.session_state.get_weather = True

    if st.session_state.get_weather:
        st.title(f"🌆 Weather Updates for {city}")
        with st.spinner("Fetching weather data..."):
            weather_data = get_weather_data(city, weather_api_key)

        if weather_data.get("cod") == 200:
            weather_condition = weather_data['weather'][0]['main']
            animation = get_weather_animation(weather_condition)
            st.markdown(f"### {icon} {weather_condition.title()}")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Temperature", f"{weather_data['main']['temp'] - 273.15:.1f} °C")
            with col2:
                st.metric("Humidity", f"{weather_data['main']['humidity']}%")
            with col3:
                st.metric("Pressure", f"{weather_data['main']['pressure']} hPa")
            with col4:
                st.metric("Wind Speed", f"{weather_data['wind']['speed']} m/s")

            lat = weather_data['coord']['lat']
            lon = weather_data['coord']['lon']
            forecast_data = get_weekly_forecast(weather_api_key, lat, lon)

            if forecast_data.get("cod") != "404":
                st.subheader("📈 Forecast Chart")
                display_forecast_chart(forecast_data)

                st.subheader("💬 AI Weather Summary")
                with st.spinner("Generating AI summary..."):
                    summary = generate_weather_description(weather_data, huggingface_api_key)
                    st.markdown(f"> {summary}")

                st.subheader("📄 Download Forecast")
                pdf_path = generate_forecast_pdf(forecast_data)
                with open(pdf_path, "rb") as f:
                    st.download_button("Download Forecast PDF", f, file_name="forecast.pdf")

            else:
                st.error("Couldn't fetch forecast data.")
        else:
            st.error(f"Error: {weather_data.get('message', 'Unknown error')}")

if __name__ == "__main__":
    main()
