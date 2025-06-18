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

# Load Lottie animations with error handling
def load_lottieurl(url, max_retries=3):
    for _ in range(max_retries):
        try:
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return r.json()
        except Exception:
            continue
    return None

# Preload Lottie animations
try:
    lottie_rainy = load_lottieurl("https://assets8.lottiefiles.com/packages/lf20_kcsr6fcp.json")
    lottie_sunny = load_lottieurl("https://assets4.lottiefiles.com/packages/lf20_pmvvvcdb.json")
    lottie_cloudy = load_lottieurl("https://assets2.lottiefiles.com/packages/lf20_1pxqjqps.json")
    lottie_weather = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_5tkzkblw.json")
except Exception as e:
    st.warning(f"Could not preload some animations: {str(e)}")
    lottie_rainy = lottie_sunny = lottie_cloudy = lottie_weather = None

# Weather data functions
def get_weather_data(city, weather_api_key):
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    complete_url = f"{base_url}appid={weather_api_key}&q={city}"
    response = requests.get(complete_url)
    return response.json()

def get_weekly_forecast(weather_api_key, lat, lon):
    forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={weather_api_key}"
    response = requests.get(forecast_url)
    return response.json()

def generate_forecast_pdf(forecast_data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Weekly Weather Forecast", ln=True, align='C')
    pdf.ln()

    displayed_dates = set()
    for item in forecast_data['list']:
        date = datetime.fromtimestamp(item['dt']).strftime('%A, %B %d')
        if date not in displayed_dates:
            displayed_dates.add(date)
            min_temp = item['main']['temp_min'] - 273.15
            max_temp = item['main']['temp_max'] - 273.15
            description = item['weather'][0]['description']
            pdf.cell(0, 10, txt=f"{date} - {description.title()} - Min: {min_temp:.1f}°C Max: {max_temp:.1f}°C", ln=True)

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
    plt.plot(dates, temps, marker='o', color='#4CAF50', linewidth=2, markersize=8)
    plt.xticks(rotation=45)
    plt.title("5-Day Temperature Forecast", fontsize=14, pad=20)
    plt.xlabel("DateTime", fontsize=12)
    plt.ylabel("Temperature (°C)", fontsize=12)
    plt.tight_layout()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.savefig("forecast_chart.png", transparent=True)
    st.image("forecast_chart.png")

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

        response = requests.post(api_url, headers=headers, json=payload)
        if response.status_code == 200:
            try:
                result = response.json()
                if isinstance(result, list) and len(result) > 0 and 'generated_text' in result[0]:
                    return result[0]['generated_text'].strip()
                return "Received weather summary from AI"
            except json.JSONDecodeError:
                return "Weather summary unavailable right now"
        return "Could not generate weather summary"
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

def main():
    st.set_page_config(
        page_title="Weather Forecast with AI", 
        page_icon="🌦",
        layout="centered", 
        initial_sidebar_state="expanded"
    )
    
    # Fixed CSS with proper syntax
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    
    body {
        font-family: 'Poppins', sans-serif;
        background-color: #f5f7fa;
        color: #333;
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .metric-container {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .metric-container:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }
    
    .metric-value {
        font-size: 24px !important;
        font-weight: 600 !important;
        color: #4CAF50 !important;
    }
    
    .metric-label {
        font-size: 14px !important;
        color: #666 !important;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(46, 125, 50, 0.4);
    }
    
    .stTextInput>div>div>input {
        border-radius: 8px !important;
        padding: 10px !important;
    }
    
    .stMarkdown h1 {
        color: #2E7D32;
        text-align: center;
        margin-bottom: 20px;
    }
    
    .stMarkdown h2 {
        color: #4CAF50;
        border-bottom: 2px solid #4CAF50;
        padding-bottom: 5px;
        margin-top: 30px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        try:
            generic_animation = load_lottieurl("https://assets10.lottiefiles.com/packages/lf20_5tkzkblw.json")
            if generic_animation:
                st_lottie(generic_animation, height=150, key="sidebar")
        except Exception:
            st.warning("Could not load sidebar animation")

        st.title("🌦 Weather Forecast")
        city = st.text_input("Enter city name", "London", key="city_input")
        
        if st.button("Get Weather", key="get_weather_btn"):
            st.session_state.get_weather = True

    if st.session_state.get_weather and city:
        try:
            st.title(f"🌆 Weather updates for {city}")
            with st.spinner('Fetching weather data...'):
                weather_data = get_weather_data(city, weather_api_key)

                if weather_data.get("cod") == 200:
                    # Display weather animation
                    weather_condition = weather_data['weather'][0]['main']
                    animation = get_weather_animation(weather_condition)
                    
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        if animation:
                            st_lottie(animation, height=200, key="weather_anim")
                    
                    with col2:
                        st.markdown(f"""
                        <div style="background: white; border-radius: 10px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                            <h2 style="color: #4CAF50; margin-top: 0;">Current Weather</h2>
                            <p style="font-size: 18px;">{weather_data['weather'][0]['description'].title()}</p>
                        </div>
                        """, unsafe_allow_html=True)

                    # Metrics
                    cols = st.columns(4)
                    metrics = [
                        ("Temperature", f"{weather_data['main']['temp'] - 273.15:.1f} °C"),
                        ("Humidity", f"{weather_data['main']['humidity']}%"),
                        ("Pressure", f"{weather_data['main']['pressure']} hPa"),
                        ("Wind Speed", f"{weather_data['wind']['speed']} m/s")
                    ]
                    
                    for col, (label, value) in zip(cols, metrics):
                        with col:
                            st.markdown(f"""
                            <div class="metric-container">
                                <div class="metric-label">{label}</div>
                                <div class="metric-value">{value}</div>
                            </div>
                            """, unsafe_allow_html=True)

                    try:
                        lat = weather_data['coord']['lat']
                        lon = weather_data['coord']['lon']
                        forecast_data = get_weekly_forecast(weather_api_key, lat, lon)
                        
                        if forecast_data.get("cod") == "200":
                            st.subheader("📈 Forecast Chart")
                            display_forecast_chart(forecast_data)

                            st.subheader("💬 AI Weather Summary")
                            with st.spinner('Generating AI summary...'):
                                description = generate_weather_description(weather_data, huggingface_api_key)
                                st.markdown(f"""
                                <div style="background: white; border-radius: 10px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                                    <p style="font-size: 16px; line-height: 1.6;">{description}</p>
                                </div>
                                """, unsafe_allow_html=True)

                            st.subheader("📄 Download Forecast")
                            pdf_path = generate_forecast_pdf(forecast_data)
                            with open(pdf_path, "rb") as file:
                                st.download_button(
                                    "Download Forecast PDF", 
                                    file, 
                                    file_name="forecast.pdf",
                                    key="download_pdf"
                                )
                    except Exception as e:
                        st.error(f"Forecast error: {str(e)}")
                else:
                    st.error(f"Weather data error: {weather_data.get('message', 'Unknown error')}")
        except Exception as e:
            st.error(f"Application error: {str(e)}")

if __name__ == "__main__":
    main()
