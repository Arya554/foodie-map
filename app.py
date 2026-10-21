import streamlit as st
import plotly.express as px
import folium
from streamlit_folium import st_folium
import utils

st.set_page_config(page_title="Restaurant Explorer India", page_icon="🍜", layout="wide")

st.title("🍜 Restaurant Explorer India")
st.markdown(
    "**Question this app answers:** does paying more get you a better-rated restaurant, "
    "and which cities and cuisines are rated best by diners?  \n"
    "Data: real Zomato dining ratings, votes and dish prices for 914 restaurants in 13 Indian cities (a snapshot, not live)."
)

r = utils.load_restaurants()

# ---------- Sidebar filters ----------
st.sidebar.header("Filters")
all_cities = sorted(r["city"].unique())
cities = st.sidebar.multiselect("City", all_cities, default=all_cities)

top_cuisines = r["cuisine"].value_counts().index.tolist()
cuisines = st.sidebar.multiselect("Cuisine (leave empty for all)", top_cuisines)

bands = list(r["price_band"].cat.categories)
sel_bands = st.sidebar.multiselect("Price range (average dish price, ₹)", bands, default=bands)

min_rating = st.sidebar.slider("Minimum dining rating", 2.5, 5.0, 2.5, 0.1)
reliable_only = st.sidebar.checkbox(
    f"Only ratings with {utils.MIN_VOTES}+ dining votes (recommended)", value=True,
    help="A rating based on a handful of votes is not trustworthy, so we hide those by default.",
)

f = r[r["city"].isin(cities) & r["price_band"].isin(sel_bands) & (r["dining_rating"] >= min_rating)]
if cuisines:
    f = f[f["cuisine"].isin(cuisines)]
if reliable_only:
    f = f[f["reliable"]]

if f.empty:
    st.warning("No restaurants match these filters. Loosen them in the sidebar.")
    st.stop()

# ---------- KPI cards ----------
c1, c2, c3 = st.columns(3)
c1.metric("Restaurants found", f"{len(f):,}")
c2.metric("Average dining rating", f"{f['dining_rating'].mean():.2f}")
c3.metric("Highly rated (4.0+)", f"{int(f['highly_rated'].sum()):,}",
          f"{f['highly_rated'].mean() * 100:.0f}% of results", delta_color="off")


# ---------- Map ----------
def rating_color(x):
    return "green" if x >= 3.95 else "orange" if x >= 3.8 else "red"


def city_map(data):
    g = data.groupby("city").agg(restaurants=("name", "count"), avg_rating=("dining_rating", "mean")).reset_index()
    m = folium.Map(location=[22.5, 79.0], zoom_start=5, tiles="OpenStreetMap")
    for _, row in g.iterrows():
        lat, lon = utils.CITY_COORDS[row["city"]]
        folium.CircleMarker(
            location=[lat, lon], radius=6 + row["restaurants"] ** 0.5,
            color=rating_color(row["avg_rating"]), fill=True, fill_opacity=0.6,
            tooltip=f"{row['city']}: {row['restaurants']} restaurants, avg rating {row['avg_rating']:.2f}",
        ).add_to(m)
    caption = (
        "One bubble per city. Bubble size = number of restaurants. "
        "Colour: green = avg 3.95+, orange = 3.8 to 3.94, red = below 3.8. "
        "Pick a city above to see its areas."
    )
    return m, caption


def area_map(data, city):
    coords = utils.load_area_coords()
    ga = data[data["city"] == city].groupby(["area", "city"]).agg(
        restaurants=("name", "count"), avg_rating=("dining_rating", "mean")
    ).reset_index().merge(coords, on=["area", "city"], how="left")
    placed = ga.dropna(subset=["lat", "lon"])
    lat0, lon0 = utils.CITY_COORDS[city]
    m = folium.Map(location=[lat0, lon0], zoom_start=11, tiles="OpenStreetMap")
    for _, row in placed.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]], radius=5 + row["restaurants"] ** 0.5 * 2,
            color=rating_color(row["avg_rating"]), fill=True, fill_opacity=0.6,
            tooltip=f"{row['area']}: {row['restaurants']} restaurants, avg rating {row['avg_rating']:.2f}",
        ).add_to(m)
    caption = (
        f"One bubble per area in {city}, placed at the approximate centre of the area, not the exact address. "
        f"Bubble size = number of restaurants, colour = average rating. "
        f"{len(placed)} of {len(ga)} areas could be located."
    )
    return m, caption


st.subheader("Where are the best-rated restaurants?")
view = st.selectbox("Map view", ["All India (one bubble per city)"] + sorted(f["city"].unique()))

if view.startswith("All India"):
    fmap, map_caption = city_map(f)
else:
    fmap, map_caption = area_map(f, view)

st_folium(fmap, height=450, width=1200, returned_objects=[])
st.caption(map_caption)

# ---------- Charts ----------
left, right = st.columns(2)

with left:
    st.subheader("Does a higher price mean a better rating?")
    band = f.groupby("price_band", observed=True)["dining_rating"].agg(["count", "mean"]).reset_index()
    band.columns = ["price_band", "restaurants", "avg_rating"]
    band["avg_rating"] = band["avg_rating"].round(2)
    fig = px.bar(band, x="price_band", y="avg_rating", text="restaurants",
                 labels={"price_band": "Price band", "avg_rating": "Average dining rating"})
    fig.update_traces(texttemplate="n=%{text}", textposition="outside")
    fig.update_yaxes(range=[3, 4.6])
    st.plotly_chart(fig, width="stretch")

with right:
    st.subheader("Price vs rating, every restaurant")
    fig2 = px.scatter(f, x="avg_dish_price", y="dining_rating", color="city",
                      hover_name="name", opacity=0.6,
                      labels={"avg_dish_price": "Average dish price (₹)", "dining_rating": "Dining rating"})
    st.plotly_chart(fig2, width="stretch")

# ---------- Insights (computed from the filtered data) ----------
st.subheader("💡 Insights")
notes = []

if len(f) >= 10:
    corr = f["avg_dish_price"].corr(f["dining_rating"])
    strength = "very weak" if abs(corr) < 0.2 else "weak" if abs(corr) < 0.4 else "moderate" if abs(corr) < 0.6 else "strong"
    notes.append(
        f"**Price and rating:** the correlation is {corr:.2f}, a {strength} relationship. "
        + ("Paying more does not reliably buy a better-rated restaurant." if abs(corr) < 0.4
           else "Higher-priced restaurants tend to be rated differently, but correlation is not causation.")
    )

big_bands = band[band["restaurants"] >= 10]
small_bands = band[band["restaurants"] < 10]
if len(big_bands) >= 2:
    hi, lo = big_bands.loc[big_bands["avg_rating"].idxmax()], big_bands.loc[big_bands["avg_rating"].idxmin()]
    notes.append(
        f"**Price bands:** among bands with at least 10 restaurants, **{hi['price_band']}** scores highest "
        f"({hi['avg_rating']:.2f}) and **{lo['price_band']}** lowest ({lo['avg_rating']:.2f}), "
        f"a gap of only {hi['avg_rating'] - lo['avg_rating']:.2f} stars."
    )
if len(small_bands):
    names = ", ".join(small_bands["price_band"].astype(str))
    notes.append(f"**Caution:** {names} has fewer than 10 restaurants here, so its average is not reliable.")

cg = f.groupby("city")["dining_rating"].agg(["count", "mean"])
cg = cg[cg["count"] >= 10]
if len(cg) >= 2:
    notes.append(
        f"**Cities (10+ restaurants):** **{cg['mean'].idxmax()}** has the highest average rating "
        f"({cg['mean'].max():.2f}) and **{cg['mean'].idxmin()}** the lowest ({cg['mean'].min():.2f}). "
        "The spread between cities is small, so treat it as a tendency, not a verdict."
    )

cu = f.groupby("cuisine")["dining_rating"].agg(["count", "mean"])
cu = cu[cu["count"] >= 8]
if len(cu) >= 2:
    notes.append(
        f"**Cuisines (8+ restaurants):** **{cu['mean'].idxmax()}** is rated highest ({cu['mean'].max():.2f}) "
        f"and **{cu['mean'].idxmin()}** lowest ({cu['mean'].min():.2f})."
    )

if notes:
    for n in notes:
        st.markdown(f"- {n}")
else:
    st.info("Too few restaurants in this selection for reliable insights. Widen the filters.")

st.caption(
    "Limits: the dataset is a snapshot. Price is the average price of dishes on the menu, not cost for two. "
    "Ratings are Zomato dining ratings; restaurants with fewer than 50 votes are hidden by default."
)

# ---------- Table + download ----------
st.subheader("Restaurant list")
show = f[["name", "city", "area", "cuisine", "dining_rating", "dining_votes", "avg_dish_price", "price_band"]]
st.dataframe(show.sort_values("dining_rating", ascending=False), width="stretch", hide_index=True)
st.download_button("⬇️ Download filtered list (CSV)", show.to_csv(index=False).encode("utf-8"),
                   file_name="restaurants_filtered.csv", mime="text/csv")