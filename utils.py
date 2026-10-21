import requests
import numpy as np
import pandas as pd
import streamlit as st

CITIES = {
    "Bengaluru": (12.9716, 77.5946),
    "Mumbai": (19.0760, 72.8777),
    "Delhi": (28.6139, 77.2090),
    "Hyderabad": (17.3850, 78.4867),
    "Chennai": (13.0827, 80.2707),
    "Pune": (18.5204, 73.8567),
}

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

FETCH_RADIUS_M = 4000


def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_restaurants(city):
    lat0, lon0 = CITIES[city]
    query = f"""
    [out:json][timeout:60];
    nwr["amenity"~"^(restaurant|cafe|fast_food)$"]["name"](around:{FETCH_RADIUS_M},{lat0},{lon0});
    out center tags 300;
    """
    headers = {
        "User-Agent": "foodie-map-student-project/1.0 (learning project)",
        "Accept": "application/json",
    }
    elements = None
    errors = []
    for url in OVERPASS_URLS:
        try:
            r = requests.post(url, data={"data": query}, headers=headers, timeout=70)
            r.raise_for_status()
            elements = r.json()["elements"]
            break
        except Exception as e:
            errors.append(f"{url.split('/')[2]}: {type(e).__name__} {str(e)[:120]}")
    if elements is None:
        raise RuntimeError("Could not reach OpenStreetMap. Details:\n\n" + "\n\n".join(errors))

    rows = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name")
        lat = el.get("lat") or el.get("center", {}).get("lat")
        lon = el.get("lon") or el.get("center", {}).get("lon")
        if not name or lat is None or lon is None:
            continue

        cuisine = tags.get("cuisine", "").split(";")[0].replace("_", " ").title() or "Unknown"

        suburb = tags.get("addr:suburb") or tags.get("addr:neighbourhood")
        if suburb:
            neighborhood, n_source = suburb, "OpenStreetMap"
        else:
            neighborhood = f"Zone {round(lat / 0.02) * 0.02:.2f}, {round(lon / 0.02) * 0.02:.2f}"
            n_source = "Estimated (grid)"

        # DEMO values: OpenStreetMap has no ratings or prices
        rng = np.random.default_rng(el["id"])
        rating = round(float(rng.uniform(3.0, 5.0)), 1)
        price_level = int(rng.integers(1, 4))

        rows.append({
            "name": name,
            "type": tags.get("amenity", "").replace("_", " ").title(),
            "cuisine": cuisine,
            "latitude": lat,
            "longitude": lon,
            "neighborhood": neighborhood,
            "neighborhood_source": n_source,
            "rating_demo": rating,
            "price_demo": "₹" * price_level,
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        df["distance_km"] = haversine_km(lat0, lon0, df["latitude"], df["longitude"]).round(2)
    return df