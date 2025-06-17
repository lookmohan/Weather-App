# 🌦 Weather Forecast with AI

An interactive and beautifully styled weather forecasting app built using **Streamlit**. It provides current weather updates, a 5-day forecast, AI-generated weather summaries, Lottie animations, and a downloadable forecast PDF.

![App Screenshot]![Weather Forecast with AI · Streamlit - Google Chrome 17-06-2025 21_26_38 (1)](https://github.com/user-attachments/assets/de03e877-3bd7-443d-9334-a247862fb02e)


---

## 🔍 Features

- 🌤 Real-time **current weather** and **5-day forecast**
- 💬 **AI-generated weather summaries** using Hugging Face
- 📉 **Temperature chart** with Matplotlib
- 📄 Export **forecast PDF**
- ✨ Lottie animations based on weather condition
- 🎨 Fully responsive with stylish UI using custom CSS

---

## 🚀 Live Demo

Check it out here:  
🔗 ([https://weather-ai-lookmohan.streamlit.app/](https://weather-app-with-ai-summary.streamlit.app/))

---

## 🧰 Tech Stack

- **Python**
- **Streamlit**
- **OpenWeatherMap API**
- **Hugging Face Inference API**
- **Matplotlib** (for plotting)
- **FPDF** (for PDF generation)
- **Lottie** (for animations)

---

## 🔐 Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/lookmohan/Weather-App.git
cd Weather-App
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.streamlit/secrets.toml`

You **must** set your API keys like this in `.streamlit/secrets.toml` (this file is **not** tracked by GitHub):

```toml
WAK = "your_openweathermap_api_key"
HAK = "your_huggingface_api_key"
```

> ✅ If deploying on [Streamlit Cloud](https://streamlit.io/cloud), add the above keys in your app’s **Settings > Secrets**.

---

## 🧪 Run the App Locally

```bash
streamlit run app.py
```

---

## 📦 Deployment

This app is fully compatible with **Streamlit Cloud**:

1. Push the code to GitHub
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
3. Click **"New App"**
4. Connect your GitHub repo
5. Set secrets under **Settings > Secrets**
6. Deploy ✅

---

## 📷 Screenshots

| Current Weather | AI Summary | Forecast Chart |
|-----------------|------------|----------------|
| ![weather](https://via.placeholder.com/250) | ![ai](https://via.placeholder.com/250) | ![chart](https://via.placeholder.com/250) |

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙌 Acknowledgements

- [OpenWeatherMap](https://openweathermap.org/)
- [Hugging Face Transformers](https://huggingface.co/)
- [LottieFiles](https://lottiefiles.com/)
- [Streamlit](https://streamlit.io/)

---

## ✨ Made with ❤️ by [Mohanraj R](https://github.com/lookmohan)
