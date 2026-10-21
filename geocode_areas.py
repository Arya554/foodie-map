import time
import requests
import numpy as np
import pandas as pd
import utils

r = utils.load_restaurants()
pairs = r[["area", "city"]].drop_duplicates().sort_values(["city", "area"]).values.tolist()
print("Areas to look up:", len(pairs))


def km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371 * 2 * np.arcsin(np.sqrt(a))


rows = []
for i, (area, city) in enumerate(pairs, 1):
    lat = lon = None
    try:
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": f"{area}, {city}, India", "format": "json", "limit": 1},
            headers={"User-Agent": "foodie-map-student-project/1.0"},
            timeout=20,
        )
        data = resp.json()
        if data:
            lat, lon = float(data[0]["lat"]), float(data[0]["lon"])
            c_lat, c_lon = utils.CITY_COORDS[city]
            if km(lat, lon, c_lat, c_lon) > 40:  # reject matches far from the city
                lat = lon = None
    except Exception as e:
        print("  error:", area, city, type(e).__name__)
    rows.append({"area": area, "city": city, "lat": lat, "lon": lon})
    print(f"{i}/{len(pairs)}  {area}, {city}  ->  {lat}, {lon}")
    time.sleep(1.1)  # the free service allows about 1 request per second

out = pd.DataFrame(rows)
out.to_csv("data/area_coords.csv", index=False)
print("\nFound:", out["lat"].notna().sum(), "of", len(out))