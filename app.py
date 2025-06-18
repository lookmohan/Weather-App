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

def generate_forecast_pdf(forecast_data, city, current_weather):
    pdf = FPDF()
    pdf.add_page()
    
    # Add title with city name
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=f"Weather Forecast Report for {city}", ln=True, align='C')
    pdf.ln(10)
    
    # Add current weather summary
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Current Weather Summary", ln=True)
    pdf.set_font("Arial", '', 12)
    
    # Current weather details
    current_temp = current_weather['main']['temp'] - 273.15
    weather_desc = current_weather['weather'][0]['description'].title()
    humidity = current_weather['main']['humidity']
    pressure = current_weather['main']['pressure']
    wind_speed = current_weather['wind']['speed']
    
    pdf.multi_cell(0, 10, txt=f"""
    Temperature: {current_temp:.1f}°C
    Conditions: {weather_desc}
    Humidity: {humidity}%
    Pressure: {pressure} hPa
    Wind Speed: {wind_speed} m/s
    """)
    
    pdf.ln(10)
    
    # Add forecast chart image
    if os.path.exists("forecast_chart.png"):
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt="5-Day Temperature Forecast", ln=True)
        pdf.image("forecast_chart.png", x=10, w=190)
        pdf.ln(10)
    
    # Detailed daily forecast
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Detailed Daily Forecast", ln=True)
    pdf.set_font("Arial", '', 12)
    
    # Group forecast by day
    daily_forecast = {}
    for item in forecast_data['list']:
        date = datetime.fromtimestamp(item['dt']).strftime('%A, %B %d')
        if date not in daily_forecast:
            daily_forecast[date] = []
        daily_forecast[date].append(item)
    
    # Add forecast for each day
    for date, forecasts in daily_forecast.items():
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, txt=date, ln=True)
        
        # Get min/max temps for the day
        min_temp = min(f['main']['temp_min'] for f in forecasts) - 273.15
        max_temp = max(f['main']['temp_max'] for f in forecasts) - 273.15
        avg_humidity = sum(f['main']['humidity'] for f in forecasts) / len(forecasts)
        
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 8, txt=f"Day Summary: High {max_temp:.1f}°C / Low {min_temp:.1f}°C | Humidity: {avg_humidity:.1f}%", ln=True)
        
        # Add hourly breakdown
        pdf.set_font("Arial", 'I', 10)
        for forecast in forecasts[:4]:  # Show first 4 time periods
            time = datetime.fromtimestamp(forecast['dt']).strftime('%H:%M')
            temp = forecast['main']['temp'] - 273.15
            desc = forecast['weather'][0]['description'].title()
            pdf.cell(0, 6, txt=f"{time}: {temp:.1f}°C, {desc}", ln=True)
        
        pdf.ln(5)
    
    # Add recommendations based on weather
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt="Weather Recommendations", ln=True)
    pdf.set_font("Arial", '', 12)
    
    if 'rain' in weather_desc.lower():
        recommendations = [
            "☔ Carry an umbrella or raincoat",
            "🚗 Allow extra time for travel as roads may be wet",
            "👟 Wear waterproof footwear",
            "📱 Check for weather alerts before going out"
        ]
    elif current_temp < 10:
        recommendations = [
            "🧥 Wear warm layers including a coat",
            "🧤 Don't forget gloves and a hat",
            "🚗 Check your vehicle's antifreeze levels",
            "🏠 Ensure your heating system is working properly"
        ]
    else:
        recommendations = [
            "🧴 Apply sunscreen if going outside",
            "💧 Stay hydrated throughout the day",
            "👒 Wear a hat to protect from the sun",
            "🕶️ Consider sunglasses for eye protection"
        ]
    
    for rec in recommendations:
        pdf.cell(0, 8, txt=f"• {rec}", ln=True)
    
    # Add footer
    pdf.ln(15)
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(0, 10, txt=f"Report generated on {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align='C')
    
    path = "forecast_report.pdf"
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
