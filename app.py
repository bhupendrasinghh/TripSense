import streamlit as st
import folium
from streamlit_folium import st_folium

from backend.geocode import geocode_place
from backend.routes import get_route
from backend.hotels import get_hotels
from backend.images import get_image
from backend.llm import generate_itinerary
from backend.wikipedia import get_wikipedia_data


# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="TripSense – Smart Travel Planner",
    page_icon="🌍",
    layout="wide"
)


# =====================================================
# CACHE HELPERS
# =====================================================
@st.cache_data
def cached_geocode(place):
    return geocode_place(place)


@st.cache_data
def cached_wiki(place):
    return get_wikipedia_data(place)


@st.cache_data
def build_map_points(city, itinerary):

    city_geo = cached_geocode(city)
    geo_points = []

    for day in itinerary:
        for act in day["activities"]:
            geo = cached_geocode(act["place"])
            if geo:
                geo_points.append(geo)

    return city_geo, geo_points


# =====================================================
# TRIP COST ESTIMATION
# =====================================================
def estimate_trip_cost(days, hotel_pref):

    hotel_prices = {
        "Budget / Hostel": 1200,
        "3 Star": 3500,
        "4 Star": 6500,
        "5 Star": 12000
    }

    stay = hotel_prices.get(hotel_pref, 3000) * days
    food = 800 * days
    transport = 600 * days
    tickets = 500 * days

    total = stay + food + transport + tickets

    return {
        "stay": stay,
        "food": food,
        "transport": transport,
        "tickets": tickets,
        "total": total
    }


# =====================================================
# UI CSS
# =====================================================
st.markdown("""
<style>

body{
    background:#f4f6f9;
}

.hero{
    position:relative;
    padding:80px;
    border-radius:26px;
    color:white;
    margin-bottom:40px;
    background-size:cover;
    background-position:center;
}

.hero-overlay{
    position:absolute;
    inset:0;
    background:rgba(0,0,0,0.55);
    border-radius:26px;
}

.hero-content{
    position:relative;
    z-index:2;
}

.hero-title{
    font-size:56px;
    font-weight:800;
}

.hero-sub{
    font-size:22px;
}

.section-title{
    font-size:32px;
    font-weight:700;
    margin-top:40px;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# HEADER
# =====================================================
st.title("🌍 TripSense – Smart Travel Planner")


# =====================================================
# INPUT SECTION
# =====================================================
c1, c2, c3 = st.columns(3)

with c1:
    city = st.text_input("Destination City")

with c2:
    days = st.slider("Trip Duration", 1, 6, 3)

with c3:
    hotel_pref = st.selectbox(
        "Hotel Preference",
        ["Budget / Hostel", "3 Star", "4 Star", "5 Star"]
    )

user_places_text = st.text_area(
    "Places to visit (optional)",
    placeholder="India Gate\nRed Fort\nQutub Minar"
)

plan_btn = st.button("🚀 Generate Smart Itinerary")


# =====================================================
# GENERATE TRIP
# =====================================================
if plan_btn and city.strip():

    with st.spinner("Creating your AI travel plan..."):

        user_places = [
            p.strip()
            for p in user_places_text.split("\n")
            if p.strip()
        ]

        itinerary = generate_itinerary(
            city=city,
            days=days,
            user_places=user_places,
            hotel_pref=hotel_pref
        )

        if not itinerary.get("itinerary"):
            st.error("Unable to generate itinerary.")
            st.stop()

        st.session_state["trip"] = itinerary


# =====================================================
# DISPLAY RESULTS
# =====================================================
if "trip" in st.session_state:

    trip = st.session_state["trip"]

    # =================================================
    # HERO
    # =================================================
    city_img = get_image(trip["city"], category="city")
    wiki_city = cached_wiki(trip["city"])

    st.markdown(f"""
    <div class='hero' style="background-image:url('{city_img}')">
        <div class='hero-overlay'></div>
        <div class='hero-content'>
            <div class='hero-title'>{trip['city']}</div>
            <div class='hero-sub'>{trip['days']} Day Travel Plan</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if wiki_city and wiki_city.get("summary"):
        st.write(wiki_city["summary"])

    if wiki_city and wiki_city.get("url"):
        st.markdown(f"[Read more on Wikipedia]({wiki_city['url']})")


    # =================================================
    # CITY MAP
    # =================================================
    st.markdown("### 📍 Places Map")

    city_geo, geo_points = build_map_points(
        trip["city"],
        trip["itinerary"]
    )

    if not city_geo:
        st.error("City not found.")
        st.stop()

    m = folium.Map(
        location=[city_geo["lat"], city_geo["lon"]],
        zoom_start=12
    )

    for g in geo_points:

        folium.Marker(
            [g["lat"], g["lon"]],
            popup=g["name"],
            icon=folium.Icon(color="red")
        ).add_to(m)

    st_folium(
        m,
        height=520,
        use_container_width=True,
        key="city_map"
    )


    # =================================================
    # ROUTE FINDER
    # =================================================
    st.markdown("### 🧭 Route Finder")

    col1, col2 = st.columns(2)

    with col1:
        start_location = st.text_input(
            "Start Location (A)",
            placeholder="Example: India Gate",
            key="start"
        )

    with col2:
        end_location = st.text_input(
            "Destination (B)",
            placeholder="Example: Red Fort",
            key="end"
        )

    route_btn = st.button("Find Route")

    if route_btn:

        geo_a = cached_geocode(start_location)
        geo_b = cached_geocode(end_location)

        if geo_a and geo_b:

            route = get_route(geo_a, geo_b)

            st.session_state["route"] = {
                "geo_a": geo_a,
                "geo_b": geo_b,
                "route": route
            }

        else:
            st.error("Location not found")


    # =================================================
    # DISPLAY ROUTE
    # =================================================
    if "route" in st.session_state:

        data = st.session_state["route"]

        geo_a = data["geo_a"]
        geo_b = data["geo_b"]
        route = data["route"]

        st.success(f"Distance: {route['distance_km']} km")
        st.success(f"Estimated Time: {route['time_min']} minutes")

        center_lat = (geo_a["lat"] + geo_b["lat"]) / 2
        center_lon = (geo_a["lon"] + geo_b["lon"]) / 2

        route_map = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=12
        )

        folium.Marker(
            [geo_a["lat"], geo_a["lon"]],
            popup="Start",
            icon=folium.Icon(color="green")
        ).add_to(route_map)

        folium.Marker(
            [geo_b["lat"], geo_b["lon"]],
            popup="Destination",
            icon=folium.Icon(color="red")
        ).add_to(route_map)

        if route.get("polyline"):

            folium.PolyLine(
                route["polyline"],
                color="blue",
                weight=6
            ).add_to(route_map)

        st_folium(
            route_map,
            height=500,
            key="route_map"
        )


    # =================================================
    # ITINERARY
    # =================================================
    st.markdown("### 🧠 AI Itinerary")

    for day in trip["itinerary"]:

        st.markdown(f"## Day {day['day']}")

        for act in day["activities"]:

            place = act["place"]
            img = get_image(place, "place")
            wiki = cached_wiki(place)

            col1, col2 = st.columns([1,2])

            with col1:
                st.image(img, use_container_width=True)

            with col2:
                st.subheader(place)

                if act.get("time"):
                    st.write(f"⏰ {act['time']}")

                st.write(act["description"])

                if wiki and wiki.get("summary"):
                    st.caption(wiki["summary"])

        st.divider()


    # =================================================
    # HOTELS
    # =================================================
    st.markdown("### 🏨 Recommended Hotels")

    hotels = get_hotels(trip["city"])

    if hotels:

        cols = st.columns(3)

        for i, h in enumerate(hotels):

            with cols[i % 3]:

                hotel_img = get_image(h["name"], "hotel")

                st.image(hotel_img, use_container_width=True)

                st.subheader(h["name"])
                st.write(h.get("address", ""))

                if h.get("distance_m"):
                    st.caption(
                        f"{round(h['distance_m']/1000,2)} km away"
                    )

                st.write(h.get("type"))


    # =================================================
    # TOTAL TRIP COST
    # =================================================
    st.markdown("### 💰 Estimated Trip Cost")

    cost = estimate_trip_cost(trip["days"], hotel_pref)

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Stay", f"₹{cost['stay']}")
    c2.metric("Food", f"₹{cost['food']}")
    c3.metric("Transport", f"₹{cost['transport']}")
    c4.metric("Tickets", f"₹{cost['tickets']}")
    c5.metric("Total", f"₹{cost['total']}")

else:
    st.info("Enter trip details above to generate your smart itinerary.")