# 🍜 Local Food & Restaurant Explorer

Interactive Streamlit app to discover restaurants, compare areas, and analyse uploaded reviews.

**Live demo:** YOUR_STREAMLIT_LINK

## Features
- Live restaurant data from OpenStreetMap (Overpass API) for 6 Indian cities
- Interactive map with colour-coded markers
- Filters: cuisine, minimum rating, price range, distance
- KPI cards, neighbourhood comparison charts (Plotly)
- Upload CSV/Excel reviews and match them with live data
- Download the filtered list as CSV
- Custom food-inspired theme

## Data note
OpenStreetMap does not provide ratings or prices, so these are **demo values**
(randomly generated, fixed per restaurant). Neighbourhoods come from OSM tags when
available, otherwise they are estimated grid zones. Real ratings come from the
reviews file the user uploads.

## Tech stack
Python, Streamlit, Pandas, Plotly, Folium, Requests

## Run locally
    pip install -r requirements.txt
    streamlit run app.py