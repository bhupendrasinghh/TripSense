# 🌍 TripSense – Smart Travel Planner

**TripSense** is an AI-powered travel planning web application built with **Streamlit** and **Groq LLM**. It generates customized day-by-day travel itineraries, interactive maps, hotel recommendations, image showcases, and trip cost breakdowns.

---

## ✨ Features

- 🤖 **AI Itinerary Generator**: Custom day-by-day itineraries using Groq LLM.
- 📍 **Interactive Maps**: Map visualization using Folium & OpenStreetMap.
- 🏨 **Hotel Recommendations**: Hotel search tailored to budget, 3-star, 4-star, or 5-star preferences.
- 📚 **Wikipedia & Image Integration**: City background info and high-res imagery via Unsplash / Pexels.
- 💰 **Cost Estimation**: Trip budget breakdowns for accommodation, food, transport, and tickets.
- 🗺️ **Custom Attractions**: Option to include specific must-visit places.

---

## 🚀 Quick Start

### 1. Clone the repository
```bash
git clone https://github.com/bhupendrasinghh/TripSense.git
cd TripSense
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up environment variables
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=your_groq_api_key
OPENTRIPMAP_API_KEY=your_opentripmap_api_key
FOURSQUARE_API_KEY=your_foursquare_api_key
UNSPLASH_API_KEY=your_unsplash_api_key
PEXELS_API_KEY=your_pexels_api_key
OPENROUTESERVICE_API_KEY=your_openrouteservice_api_key
```

### 4. Run the app
```bash
streamlit run app.py
```

---

## 🛠️ Tech Stack

- **Frontend**: Streamlit, Streamlit-Folium
- **AI & APIs**: Groq API, Nominatim Geocoding, Foursquare, Unsplash/Pexels, Wikipedia API
- **Language**: Python 3.10+
