import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import plotly.express as px
import utils

st.set_page_config(page_title="Neighborhood Analysis", page_icon="📍", layout="wide")

st.title("📍 Neighborhood Analysis")
st.markdown(
    "**Question this page answers:** within a city, which areas are rated best, "
    "and which areas have many restaurants but weaker ratings?"
)

r = utils.load_restaurants()

# ---------- City comparison (enough data for real conclusions) ----------
st.subheader("Step 1: How do cities compare?")
cr = r[r["reliable"]]
cities_df = cr.groupby("city").agg(
    restaurants=("name", "count"),
    avg_rating=("dining_rating", "mean"),
    pct_highly_rated=("highly_rated", "mean"),
    avg_price=("avg_dish_price", "mean"),
).reset_index()
cities_df = cities_df[cities_df["restaurants"] >= 10]
cities_df["avg_rating"] = cities_df["avg_rating"].round(2)
cities_df["pct_highly_rated"] = (cities_df["pct_highly_rated"] * 100).round(0)
cities_df["avg_price"] = cities_df["avg_price"].round(0)

fig_c = px.bar(cities_df.sort_values("avg_rating"), x="avg_rating", y="city", orientation="h",
               text="restaurants", labels={"avg_rating": "Average dining rating", "city": ""})
fig_c.update_traces(texttemplate="n=%{text}", textposition="outside")
fig_c.update_xaxes(range=[3.5, 4.2])
st.plotly_chart(fig_c, width="stretch")

top_c = cities_df.loc[cities_df["avg_rating"].idxmax()]
low_c = cities_df.loc[cities_df["avg_rating"].idxmin()]
cheap_c = cities_df.loc[cities_df["avg_price"].idxmin()]
st.markdown(
    f"**What this shows:** among cities with at least 10 well-reviewed restaurants, **{top_c['city']}** has the "
    f"highest average rating ({top_c['avg_rating']:.2f}) and **{low_c['city']}** the lowest "
    f"({low_c['avg_rating']:.2f}). The gap is only {top_c['avg_rating'] - low_c['avg_rating']:.2f} stars, so cities "
    f"are rated quite similarly. **{cheap_c['city']}** has the lowest average dish price (₹{cheap_c['avg_price']:.0f}). "
    "Goa is excluded because too few of its restaurants have enough votes."
)
st.divider()
st.subheader("Step 2: Zoom into one city's areas")

# ---------- Controls ----------
city = st.sidebar.selectbox("City", sorted(r["city"].unique()), index=sorted(r["city"].unique()).index("Bangalore"))
min_n = st.sidebar.slider("Minimum restaurants per area", 1, 10, 2,
                          help="Averages from very few restaurants are not reliable, so small areas are hidden.")
reliable_only = st.sidebar.checkbox(
    f"Only ratings with {utils.MIN_VOTES}+ dining votes (recommended)", value=False)

d = r[r["city"] == city]
if reliable_only:
    d = d[d["reliable"]]

if d.empty:
    st.warning("No restaurants match these settings.")
    st.stop()

# ---------- Area table ----------
areas = d.groupby("area").agg(
    restaurants=("name", "count"),
    avg_rating=("dining_rating", "mean"),
    highly_rated=("highly_rated", "sum"),
    avg_price=("avg_dish_price", "mean"),
).reset_index()
areas["avg_rating"] = areas["avg_rating"].round(2)
areas["avg_price"] = areas["avg_price"].round(0)
areas["pct_highly_rated"] = (areas["highly_rated"] / areas["restaurants"] * 100).round(0)

shown = areas[areas["restaurants"] >= min_n]

# ---------- KPI cards ----------
c1, c2, c3 = st.columns(3)
c1.metric("Areas in this city", len(areas))
c2.metric(f"Areas with {min_n}+ restaurants", len(shown))
c3.metric("City average rating", f"{d['dining_rating'].mean():.2f}")

if shown.empty:
    st.info("No area has that many restaurants. Lower the slider in the sidebar.")
    st.stop()

# ---------- Chart 1: ratings by area ----------
st.subheader(f"Average rating by area in {city}")
top = shown.sort_values("avg_rating", ascending=True)
fig = px.bar(top, x="avg_rating", y="area", orientation="h", text="restaurants",
             labels={"avg_rating": "Average dining rating", "area": ""})
fig.update_traces(texttemplate="n=%{text}", textposition="outside")
fig.update_xaxes(range=[3, 4.6])
st.plotly_chart(fig, width="stretch")

best = shown.loc[shown["avg_rating"].idxmax()]
worst = shown.loc[shown["avg_rating"].idxmin()]
st.markdown(
    f"**What this shows:** among areas with at least {min_n} restaurants, **{best['area']}** has the highest "
    f"average rating ({best['avg_rating']:.2f}, {int(best['restaurants'])} restaurants) and **{worst['area']}** "
    f"the lowest ({worst['avg_rating']:.2f}, {int(worst['restaurants'])} restaurants). The label n= is the number "
    "of restaurants behind each bar. Areas with a small n can swing a lot with one restaurant."
)

# ---------- Chart 2: crowded vs well rated ----------
st.subheader("Crowded or well rated? Restaurant count vs rating")
fig2 = px.scatter(shown, x="restaurants", y="avg_rating", size="restaurants", hover_name="area",
                  labels={"restaurants": "Number of restaurants", "avg_rating": "Average dining rating"})
city_avg = d["dining_rating"].mean()
fig2.add_hline(y=city_avg, line_dash="dash", annotation_text=f"city average {city_avg:.2f}")
st.plotly_chart(fig2, width="stretch")

busy = shown[shown["restaurants"] >= shown["restaurants"].median()]
busy_low = busy[busy["avg_rating"] < city_avg]
quiet_high = shown[(shown["restaurants"] < shown["restaurants"].median()) & (shown["avg_rating"] > city_avg)]

lines = []
if len(shown) >= 4:
    corr = shown["restaurants"].corr(shown["avg_rating"])
    lines.append(f"The correlation between the number of restaurants and the average rating is {corr:.2f}. "
                 + ("Busier areas are not clearly rated better or worse." if abs(corr) < 0.3
                    else "There is a visible link, but with this few areas it is only a hint."))
if len(busy_low):
    lines.append("**Busy but below the city average:** " + ", ".join(busy_low["area"]) +
                 ". Competition is high and ratings are mediocre, so a new restaurant faces a tough market here.")
if len(quiet_high):
    lines.append("**Fewer restaurants but above the city average:** " + ", ".join(quiet_high["area"]) +
                 ". Diners like what is there, so these look like promising gaps.")

st.markdown("**What this shows:**")
if lines:
    for line in lines:
        st.markdown(f"- {line}")
else:
    st.markdown("- Not enough areas to draw a conclusion. Lower the minimum in the sidebar.")

# ---------- Chart 3: price by area ----------
st.subheader("Are the best-rated areas also the expensive ones?")
fig3 = px.scatter(shown, x="avg_price", y="avg_rating", hover_name="area", text="area",
                  labels={"avg_price": "Average dish price (₹)", "avg_rating": "Average dining rating"})
fig3.update_traces(textposition="top center")
st.plotly_chart(fig3, width="stretch")
if len(shown) >= 4:
    pc = shown["avg_price"].corr(shown["avg_rating"])
    st.markdown(f"**What this shows:** across areas, the correlation between average price and average rating is "
                f"{pc:.2f}. " + ("Expensive areas are not reliably better rated." if abs(pc) < 0.3
                                 else "Pricier areas tend to differ in rating, but this is correlation, not cause."))

# ---------- Table + download ----------
st.subheader("Area table")
table = shown.sort_values("avg_rating", ascending=False)
st.dataframe(table, width="stretch", hide_index=True)
st.download_button("⬇️ Download area table (CSV)", table.to_csv(index=False).encode("utf-8"),
                   file_name=f"areas_{city.lower()}.csv", mime="text/csv")

st.caption("Data: Zomato dining ratings (snapshot). Only restaurants with enough votes are counted when the "
           "sidebar box is ticked. Findings describe this dataset, not every restaurant in the city.")

st.caption("Area averages here use few restaurants each, so read them as hints, not rankings. "
           "Tick the sidebar box to keep only ratings with 50+ votes (fewer areas, more reliable).")