import streamlit as st
import folium
from streamlit_folium import st_folium
import utils

st.set_page_config(page_title="Local Food & Restaurant Explorer", page_icon="🍜", layout="wide")
st.title("🍜 Local Food & Restaurant Explorer")
st.caption(
    "Live restaurant data from OpenStreetMap (Overpass API). "
    "⚠️ Ratings and price levels are DEMO values, because OpenStreetMap does not provide them."
)

# ---------- Sidebar ----------
st.sidebar.header("Filters")
city = st.sidebar.selectbox("City", list(utils.CITIES.keys()))

with st.spinner("Fetching live restaurant data..."):
    try:
        df = utils.fetch_restaurants(city)
    except Exception as e:
        st.error(str(e))
        st.stop()

if df.empty:
    st.warning("No restaurants found for this city.")
    st.stop()

st.session_state["df"] = df
st.session_state["city"] = city

cuisines = sorted(df["cuisine"].unique())
sel_cuisines = st.sidebar.multiselect("Cuisine", cuisines, default=cuisines)
min_rating = st.sidebar.slider("Minimum rating (demo)", 3.0, 5.0, 3.0, 0.1)
prices = ["₹", "₹₹", "₹₹₹"]
sel_prices = st.sidebar.multiselect("Price range (demo)", prices, default=prices)
max_dist = st.sidebar.slider("Max distance from city centre (km)", 1, 4, 4)

f = df[
    df["cuisine"].isin(sel_cuisines)
    & (df["rating_demo"] >= min_rating)
    & df["price_demo"].isin(sel_prices)
    & (df["distance_km"] <= max_dist)
]

# ---------- KPI cards ----------
c1, c2, c3 = st.columns(3)
c1.metric("Restaurants found", len(f))
c2.metric("Average rating (demo)", f"{f['rating_demo'].mean():.2f}" if len(f) else "N/A")
c3.metric("Highly rated (4.0+)", int((f["rating_demo"] >= 4.0).sum()))

# ---------- Map ----------
st.subheader("Map")
lat0, lon0 = utils.CITIES[city]
m = folium.Map(location=[lat0, lon0], zoom_start=13)
for _, r in f.iterrows():
    color = "green" if r["rating_demo"] >= 4.5 else "orange" if r["rating_demo"] >= 4.0 else "red"
    folium.CircleMarker(
        location=[r["latitude"], r["longitude"]],
        radius=6,
        color=color,
        fill=True,
        fill_opacity=0.8,
        popup=f"{r['name']}<br>{r['cuisine']}<br>Rating (demo): {r['rating_demo']}<br>{r['price_demo']}",
        tooltip=r["name"],
    ).add_to(m)
st_folium(m, height=500, use_container_width=True, returned_objects=[])
st.caption("Marker colour: green = 4.5+, orange = 4.0 to 4.4, red = below 4.0")

# ---------- Table + download ----------
st.subheader("Restaurant list")
show_cols = ["name", "type", "cuisine", "neighborhood", "rating_demo", "price_demo", "distance_km"]
st.dataframe(f[show_cols], use_container_width=True, hide_index=True)

st.download_button(
    "⬇️ Download filtered list (CSV)",
    f.to_csv(index=False).encode("utf-8"),
    file_name=f"restaurants_{city.lower()}.csv",
    mime="text/csv",
)