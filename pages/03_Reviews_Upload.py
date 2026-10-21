import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import re
from collections import Counter
import pandas as pd
import streamlit as st
import plotly.express as px
import utils

st.set_page_config(page_title="Reviews & Upload", page_icon="📝", layout="wide")

st.title("📝 Reviews & Upload")
st.markdown(
    "**Question this page answers:** how trustworthy are restaurant ratings, "
    "and what do diners' own words say when you upload their reviews?"
)

r = utils.load_restaurants()

# =====================================================
# Part 1: how reliable are the ratings in the dataset?
# =====================================================
st.header("Part 1: How reliable are the ratings?")
rated = r[r["dining_votes"] > 0]
low_share = (r["dining_votes"] < utils.MIN_VOTES).mean() * 100

c1, c2, c3 = st.columns(3)
c1.metric("Restaurants in dataset", f"{len(r):,}")
c2.metric("With zero dining votes", f"{int((r['dining_votes'] == 0).sum()):,}")
c3.metric(f"With under {utils.MIN_VOTES} votes", f"{low_share:.0f}%")

left, right = st.columns(2)
with left:
    fig = px.histogram(rated, x="dining_rating", nbins=20,
                       labels={"dining_rating": "Dining rating"}, title="Rating distribution")
    st.plotly_chart(fig, width="stretch")
with right:
    fig2 = px.scatter(rated, x="dining_votes", y="dining_rating", log_x=True, opacity=0.5,
                      hover_name="name", color="city",
                      labels={"dining_votes": "Dining votes (log scale)", "dining_rating": "Dining rating"},
                      title="More votes, more stable rating")
    st.plotly_chart(fig2, width="stretch")

few = rated[rated["dining_votes"] < utils.MIN_VOTES]["dining_rating"]
many = rated[rated["dining_votes"] >= utils.MIN_VOTES]["dining_rating"]
st.markdown("**What this shows:**")
st.markdown(
    f"- Most restaurants are rated between {rated['dining_rating'].quantile(0.25):.1f} and "
    f"{rated['dining_rating'].quantile(0.75):.1f}; the median is {rated['dining_rating'].median():.1f}."
)
st.markdown(
    f"- {low_share:.0f}% of restaurants have fewer than {utils.MIN_VOTES} dining votes, so their rating can "
    "move a lot with one or two reviews."
)
if len(few) and len(many):
    st.markdown(
        f"- In the scatter plot, ratings of low-vote restaurants spread from {few.min():.1f} to {few.max():.1f} "
        f"(std {few.std():.2f}), while restaurants with {utils.MIN_VOTES}+ votes are tighter "
        f"(std {many.std():.2f}). That is why the other pages hide low-vote ratings by default."
    )

st.divider()

# =====================================================
# Part 2: upload your own reviews
# =====================================================
st.header("Part 2: Upload and analyse your own reviews")
file = st.file_uploader("Upload a reviews file (CSV or Excel)", type=["csv", "xlsx"])

if file is None:
    st.info("Upload a file with at least a rating column. A review text column and a restaurant name column "
            "unlock more analysis.")
    st.stop()

try:
    if file.name.lower().endswith(".csv"):
        try:
            reviews = pd.read_csv(file)
        except UnicodeDecodeError:
            file.seek(0)
            reviews = pd.read_csv(file, encoding="latin-1")
    else:
        reviews = pd.read_excel(file)
except Exception as e:
    st.error(f"Could not read the file: {e}")
    st.stop()

st.subheader("Preview")
st.dataframe(reviews.head(50), width="stretch")

cols = list(reviews.columns)
none = "(none)"
rating_col = st.selectbox("Rating column", cols)
text_col = st.selectbox("Review text column (optional)", [none] + cols)
name_col = st.selectbox("Restaurant name column (optional)", [none] + cols)

reviews["_rating"] = pd.to_numeric(reviews[rating_col], errors="coerce")
reviews = reviews.dropna(subset=["_rating"])
if reviews.empty:
    st.error("The chosen rating column has no numbers in it. Pick a different column.")
    st.stop()

c1, c2, c3 = st.columns(3)
c1.metric("Reviews analysed", f"{len(reviews):,}")
c2.metric("Average rating", f"{reviews['_rating'].mean():.2f}")
c3.metric("Share rated 4+", f"{(reviews['_rating'] >= 4).mean() * 100:.0f}%")

fig3 = px.histogram(reviews, x="_rating", nbins=10, labels={"_rating": "Rating"},
                    title="Rating distribution of your reviews")
st.plotly_chart(fig3, width="stretch")
avg = reviews["_rating"].mean()
st.markdown(
    f"**What this shows:** the average rating is {avg:.2f} and {(reviews['_rating'] >= 4).mean() * 100:.0f}% of "
    f"reviews are 4 or above, while {(reviews['_rating'] <= 2).mean() * 100:.0f}% are 2 or below. "
    + ("Ratings lean positive, which is typical: unhappy diners review less often." if avg >= 3.8
       else "Ratings are mixed to negative, so there are real complaints worth reading." if avg < 3.2
       else "Ratings are moderate, so reading the text will show what separates good from bad visits.")
)

# ---------- Text analysis ----------
if text_col != none:
    st.subheader("What diners talk about")
    STOP = set("the a an and or but is was were are it its this that for with of to in on at i we you they my "
               "our me so very just have had has be been as from not no too also really there their them than "
               "then when what which who will would can could one get got all out up if do did food place "
               "restaurant order ordered".split())
    POS = set("good great excellent amazing delicious tasty fresh friendly best love loved awesome nice "
              "perfect yummy lovely superb wonderful recommend recommended".split())
    NEG = set("bad worst poor slow cold stale rude dirty bland overpriced terrible awful disappointing "
              "disappointed horrible waste tasteless raw expensive".split())

    texts = reviews[text_col].fillna("").astype(str)
    words_per_review = texts.str.lower().apply(lambda t: re.findall(r"[a-z']{3,}", t))
    counts = Counter(w for ws in words_per_review for w in ws if w not in STOP)

    top = pd.DataFrame(counts.most_common(15), columns=["word", "count"])
    if top.empty:
        st.info("No readable words found in that column.")
    else:
        fig4 = px.bar(top.sort_values("count"), x="count", y="word", orientation="h",
                      title="Most common words")
        st.plotly_chart(fig4, width="stretch")
        st.markdown(
            f"**What this shows:** the most frequent words are {', '.join(top['word'].head(5))}. "
            "Frequent words point to what diners care about most (taste, service, price, wait time)."
        )

    def sentiment(ws):
        p = sum(w in POS for w in ws)
        n = sum(w in NEG for w in ws)
        return "Positive" if p > n else "Negative" if n > p else "Neutral"

    reviews["sentiment"] = words_per_review.apply(sentiment).values
    sc = reviews["sentiment"].value_counts().reset_index()
    sc.columns = ["sentiment", "reviews"]
    fig5 = px.bar(sc, x="sentiment", y="reviews", title="Simple word-based sentiment")
    st.plotly_chart(fig5, width="stretch")

    by_sent = reviews.groupby("sentiment")["_rating"].mean().round(2).to_dict()
    st.markdown(
        "**What this shows:** each review is labelled by counting positive and negative words from a small "
        f"word list. Average rating by label: {by_sent}. If positive reviews have clearly higher ratings, the "
        "text and the stars agree. This is a basic method: it misses sarcasm and negation (\"not good\")."
    )

# ---------- Per-restaurant ----------
if name_col != none:
    st.subheader("Restaurants in your file")
    per = reviews.groupby(name_col)["_rating"].agg(["count", "mean"]).reset_index()
    per.columns = ["restaurant", "reviews", "avg_rating"]
    per["avg_rating"] = per["avg_rating"].round(2)
    enough = per[per["reviews"] >= 3]
    if len(enough) >= 2:
        best = enough.loc[enough["avg_rating"].idxmax()]
        worst = enough.loc[enough["avg_rating"].idxmin()]
        st.markdown(
            f"**What this shows:** among restaurants with at least 3 reviews, **{best['restaurant']}** is rated "
            f"highest ({best['avg_rating']:.2f}) and **{worst['restaurant']}** lowest ({worst['avg_rating']:.2f})."
        )
    else:
        st.caption("Fewer than 2 restaurants have 3+ reviews, so no best or worst is declared.")
    st.dataframe(per.sort_values("avg_rating", ascending=False), width="stretch", hide_index=True)

    m = per.copy()
    m["key"] = m["restaurant"].astype(str).str.lower().str.strip()
    ref = r.copy()
    ref["key"] = ref["name"].str.lower().str.strip()
    merged = m.merge(ref[["key", "city", "area", "cuisine", "dining_rating", "dining_votes"]],
                     on="key", how="inner").drop(columns="key")
    st.subheader("Matched with the Zomato dataset")
    if merged.empty:
        st.caption("None of your restaurant names match the dataset.")
    else:
        merged["difference"] = (merged["avg_rating"] - merged["dining_rating"]).round(2)
        st.dataframe(merged, width="stretch", hide_index=True)
        st.markdown(
            f"**What this shows:** {len(merged)} restaurants match. On average your reviewers rate them "
            f"{merged['difference'].mean():+.2f} stars versus the Zomato dining rating."
        )

st.caption("Findings describe the data you uploaded and this dataset snapshot, not all diners.")