import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Reviews & Upload", page_icon="📝", layout="wide")
st.title("📝 Reviews & Upload")

file = st.file_uploader("Upload your reviews (CSV or Excel)", type=["csv", "xlsx"])
if file is None:
    st.info("Upload a file with columns like: restaurant name, rating, review text.")
    st.stop()

reviews = pd.read_csv(file) if file.name.endswith(".csv") else pd.read_excel(file)
st.subheader("Preview")
st.dataframe(reviews.head(50), use_container_width=True)

cols = list(reviews.columns)
rating_col = st.selectbox("Which column is the rating?", cols)
reviews[rating_col] = pd.to_numeric(reviews[rating_col], errors="coerce")

c1, c2 = st.columns(2)
c1.metric("Reviews uploaded", len(reviews))
c2.metric("Average rating", f"{reviews[rating_col].mean():.2f}")

st.plotly_chart(px.histogram(reviews, x=rating_col, title="Rating distribution"), use_container_width=True)

name_col = st.selectbox("Which column is the restaurant name? (optional)", ["(none)"] + cols)
if name_col != "(none)":
    per = reviews.groupby(name_col)[rating_col].agg(["count", "mean"]).reset_index()
    per.columns = [name_col, "reviews", "avg_rating"]
    st.subheader("Average rating per restaurant")
    st.dataframe(per.sort_values("avg_rating", ascending=False), use_container_width=True, hide_index=True)

    df = st.session_state.get("df")
    if df is not None:
        merged = per.merge(df[["name", "cuisine", "neighborhood"]],
                           left_on=name_col, right_on="name", how="inner")
        st.subheader("Matched with live restaurant data")
        if merged.empty:
            st.caption("No uploaded restaurant names matched the fetched list for this city.")
        else:
            st.dataframe(merged, use_container_width=True, hide_index=True)