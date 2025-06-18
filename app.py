import streamlit as st
import requests
import json
from datetime import datetime
from fpdf import FPDF
import matplotlib.pyplot as plt
import os
from streamlit_lottie import st_lottie
import pandas as pd
from io import BytesIO

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

# Helper to choose icon for weather
def get_icon_path(desc):
    desc = desc.lower()
    if "clear" in desc:
        return "icons/sunny.png"
    elif "rain" in desc:
        return "icons/rainy.png"
    elif "cloud" in desc:
        return "icons/cloudy.png"
    else:
        return "icons/weather.png"  # default icon

# Function to generate PDF with images, AI summary, and chart
def generate_forecast_pdf(data, summary_text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=14)
    pdf.cell(200, 10, txt="Weekly Weather Forecast 📅", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.ln()

    # Metadata
    city = data['city']['name']
    country = data['city']['country']
    now = datetime.now().strftime("%A, %B %d, %Y %I:%M %p")
    pdf.cell(0, 10, txt=f"Location: {city}, {country}", ln=True)
    pdf.cell(0, 10, txt=f"Report Generated: {now}", ln=True)
    pdf.ln(5)

    # Add daily forecast with icons
    seen_dates = set()
    for item in data['list']:
        date = datetime.fromtimestamp(item['dt']).strftime('%A, %B %d')
        if date not in seen_dates:
            seen_dates.add(date)
            min_temp = item['main']['temp_min'] - 273.15
            max_temp = item['main']['temp_max'] - 273.15
            desc = item['weather'][0]['description'].title()
            icon_path = get_icon_path(desc)

            # Icon
            if os.path.exists(icon_path):
                pdf.image(icon_path, x=10, y=pdf.get_y(), w=10, h=10)
                pdf.set_xy(22, pdf.get_y())

            pdf.multi_cell(0, 10, f"{date} - {desc} - Min: {min_temp:.1f}°C Max: {max_temp:.1f}°C")
            pdf.ln(1)

    # Add weather chart
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="📈 Temperature Forecast Chart", ln=True, align='C')

    # Plot chart and save as temp
    dates = []
    temps = []
    for item in data['list']:
        dates.append(datetime.fromtimestamp(item['dt']).strftime('%d %b %H:%M'))
        temps.append(item['main']['temp'] - 273.15)

    plt.figure(figsize=(10, 4))
    plt.plot(dates, temps, marker='o', color='blue')
    plt.xticks(rotation=45)
    plt.title("Hourly Forecast")
    plt.xlabel("Time")
    plt.ylabel("Temperature (°C)")
    plt.tight_layout()
    plt.grid(True)
    chart_path = "forecast_chart_temp.png"
    plt.savefig(chart_path, dpi=150)
    plt.close()

    if os.path.exists(chart_path):
        pdf.image(chart_path, x=10, y=40, w=180)

    # AI Summary
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="🤖 AI-Generated Weather Summary", ln=True, align='C')
    pdf.set_font("Arial", '', 12)
    pdf.multi_cell(0, 10, summary_text or "No summary available.")

    # Save PDF
    output_path = "forecast_enhanced.pdf"
    pdf.output(output_path)
    return output_path

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
                    summary = generate_weather_description(weather, huggingface_api_key)
                    st.write(summary)

                    pdf_path = generate_forecast_pdf(forecast, summary)
                    with open(pdf_path, "rb") as f:
                        st.download_button("📄 Download Forecast PDF", f, file_name="forecast.pdf")

            except Exception as e:
                st.error(f"Forecast error: {str(e)}")

if __name__ == "__main__":
    main()
