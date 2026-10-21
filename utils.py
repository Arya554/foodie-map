import pandas as pd
import streamlit as st

DATA_PATH = "data/restaurants.csv"
MIN_VOTES = 50  # ratings with fewer dining votes are treated as unreliable

# Approximate city centres, used only to place one bubble per city on the map
CITY_COORDS = {
    "Hyderabad": (17.3850, 78.4867), "Jaipur": (26.9124, 75.7873),
    "Chennai": (13.0827, 80.2707), "Bangalore": (12.9716, 77.5946),
    "Mumbai": (19.0760, 72.8777), "Ahmedabad": (23.0225, 72.5714),
    "Kochi": (9.9312, 76.2673), "Kolkata": (22.5726, 88.3639),
    "Pune": (18.5204, 73.8567), "Lucknow": (26.8467, 80.9462),
    "Raipur": (21.2514, 81.6296), "Goa": (15.2993, 74.1240),
    "New Delhi": (28.6139, 77.2090),
}

# In the raw file, these Bengaluru areas were entered in the City column
MISFILED_BANGALORE = ["Ulsoor", "Banaswadi", "Magrath Road", "Malleshwaram"]


@st.cache_data
def load_items():
    """One row per menu item (cleaned)."""
    df = pd.read_csv(DATA_PATH, encoding="latin-1")
    df["City"] = df["City"].astype(str).str.strip()
    df["City"] = df["City"].replace({a: "Bangalore" for a in MISFILED_BANGALORE})
    return df


@st.cache_data
def load_restaurants():
    """One row per restaurant."""
    df = load_items()
    r = df.groupby(["Restaurant_Name", "Place_Name", "City"]).agg(
        cuisine=("Cuisine", "first"),
        dining_rating=("Dining_Rating", "first"),
        delivery_rating=("Delivery_Rating", "first"),
        dining_votes=("Dining_Votes", "first"),
        delivery_votes=("Delivery_Votes", "first"),
        avg_dish_price=("Prices", "mean"),
        dishes=("Item_Name", "count"),
    ).reset_index()
    r = r.rename(columns={"Restaurant_Name": "name", "Place_Name": "area", "City": "city"})
    r["avg_dish_price"] = r["avg_dish_price"].round(0)
    r["reliable"] = r["dining_votes"] >= MIN_VOTES
    r["highly_rated"] = r["dining_rating"] >= 4.0
    r["price_band"] = pd.cut(
        r["avg_dish_price"], bins=[0, 150, 250, 400, 5000],
        labels=["Budget (<150)", "Mid (150-250)", "Upper (250-400)", "Premium (400+)"],
    )
    return r



@st.cache_data
def load_area_coords():
    """Approximate centre of each area (looked up once with geocode_areas.py)."""
    return pd.read_csv("data/area_coords.csv").dropna(subset=["lat", "lon"])