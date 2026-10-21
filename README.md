# 🍜 Restaurant Explorer India

An interactive Streamlit dashboard that analyses Zomato restaurant data from 13 Indian cities.

**Live demo:** (https://foodie-map-4aai57falftj5gcwnbrgkz.streamlit.app/Neighborhood_Analysis)

## Problem statement
Does paying more get you a better-rated restaurant? Which cities and areas are rated best, and how much
can we trust a rating that has few votes?

## Data
- **Source:** enhanced_zomato_dta_clean from kaggle 
- 123,657 menu-item rows, grouped into **914 restaurants** across 13 cities.
- Fields used: dining rating, dining votes, cuisine, area, city, dish prices.
- **Cleaning:** four Bengaluru areas (Ulsoor, Banaswadi, Magrath Road, Malleshwaram) were wrongly entered as
  cities and were merged into Bangalore. Restaurants with fewer than 50 dining votes are treated as unreliable.
- **Price** is the average price of a restaurant's menu dishes, not cost for two.
- **Map:** the dataset has no coordinates. City bubbles use approximate city centres; area bubbles use
  approximate area centres looked up once with OpenStreetMap's Nominatim (283 of 327 areas found).

## Key findings
- Price and rating are only weakly related (correlation 0.13 across all 914 restaurants).
- Among restaurants with 50+ votes, average rating is almost flat across Budget (3.81), Mid (3.89) and
  Upper (3.87) price bands. The Premium band (4.28) has only 9 restaurants, so it is not conclusive.
- City averages (50+ votes, 10+ restaurants) range from 3.74 (Kolkata) to 4.03 (Raipur), a small gap.
- Only 334 of 914 restaurants (37%) have 50+ dining votes, and the median restaurant has 11 votes,
  so low-vote ratings should not be trusted.

## Pages
1. **Discover:** filters, KPI cards, city/area map, price-vs-rating charts, computed insights, CSV download.
2. **Neighborhood Analysis:** compares cities and areas, with written interpretations.
3. **Reviews & Upload:** rating reliability analysis, plus upload of your own CSV/Excel reviews
   (rating distribution, common words, simple sentiment, comparison with the dataset).

## Limitations
Dataset is a snapshot. Few restaurants per area in some cities. Sentiment uses a small word list and misses
sarcasm. Findings describe this dataset, not every restaurant.

## Run locally
    pip install -r requirements.txt
    streamlit run app.py

## Tech stack
Python, Streamlit, Pandas, Plotly, Folium

Built by Sakshi