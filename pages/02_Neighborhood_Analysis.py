import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Neighborhood Analysis", page_icon="📍", layout="wide")
st.title("📍 Neighborhood Analysis")

df = st.session_state.get("df")
if df is None:
    st.info("Open the Discover page first so restaurant data can load.")
    st.stop()

st.caption(
    f"City: {st.session_state['city']}. Neighborhood names come from OpenStreetMap when available; "
    "otherwise they are estimated grid zones. Ratings are demo values."
)

g = df.groupby("neighborhood").agg(
    restaurants=("name", "count"),
    avg_rating=("rating_demo", "mean"),
    highly_rated=("rating_demo", lambda s: (s >= 4.0).sum()),
).reset_index()
g["avg_rating"] = g["avg_rating"].round(2)

min_count = st.slider("Only show areas with at least this many restaurants", 1, 20, 3)
g = g[g["restaurants"] >= min_count]

if g.empty:
    st.warning("No areas match. Lower the slider.")
    st.stop()

left, right = st.columns(2)
with left:
    top = g.sort_values("restaurants", ascending=False).head(15)
    st.plotly_chart(px.bar(top, x="restaurants", y="neighborhood", orientation="h",
                           title="Restaurant count by area"), use_container_width=True)
with right:
    top = g.sort_values("avg_rating", ascending=False).head(15)
    st.plotly_chart(px.bar(top, x="avg_rating", y="neighborhood", orientation="h",
                           title="Average rating by area (demo)"), use_container_width=True)

top = g.sort_values("highly_rated", ascending=False).head(15)
st.plotly_chart(px.bar(top, x="highly_rated", y="neighborhood", orientation="h",
                       title="Highly rated (4.0+) restaurants by area"), use_container_width=True)

st.dataframe(g.sort_values("restaurants", ascending=False), use_container_width=True, hide_index=True)