import time
import requests
import pandas as pd
from datetime import date, timedelta
from pathlib import Path

CITIES = {
    "Delhi": (28.61, 77.21, "North"), "Lucknow": (26.85, 80.95, "North"),
    "Kanpur": (26.45, 80.33, "North"), "Patna": (25.59, 85.14, "North"),
    "Jaipur": (26.91, 75.79, "North"),
    "Hyderabad": (17.38, 78.48, "South"), "Chennai": (13.08, 80.27, "South"),
    "Bengaluru": (12.97, 77.59, "South"), "Visakhapatnam": (17.69, 83.22, "South"),
    "Coimbatore": (11.02, 76.96, "South"),
}

WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
AIR_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

WEATHER_MAP = {
    "temperature_2m_mean": "temperature",
    "relative_humidity_2m_mean": "humidity",
    "rain_sum": "rainfall",
    "surface_pressure_mean": "pressure",
    "wind_speed_10m_mean": "wind_speed",
    "wind_direction_10m_dominant": "wind_direction",
}
AIR_MAP = {
    "pm2_5": "pm25", "pm10": "pm10", "carbon_monoxide": "co",
    "nitrogen_dioxide": "no2", "sulphur_dioxide": "so2",
    "ozone": "o3", "us_aqi": "aqi",
}

END = date.today() - timedelta(days=5)
START = END.replace(year=END.year - 4)

def get_json(url, params, retries=5):
    for i in range(retries):
        r = requests.get(url, params=params, timeout=120)
        if r.status_code == 429:
            time.sleep(30 * (i + 1))
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("Too many retries")

def fetch_weather_daily(lat, lon):
    params = {"latitude": lat, "longitude": lon,
              "start_date": START.isoformat(), "end_date": END.isoformat(),
              "daily": ",".join(WEATHER_MAP), "timezone": "Asia/Kolkata"}
    return pd.DataFrame(get_json(WEATHER_URL, params)["daily"]).rename(columns=WEATHER_MAP)

def fetch_air_hourly(lat, lon):
    frames, cur = [], START
    while cur <= END:
        chunk_end = min(cur + timedelta(days=364), END)
        params = {"latitude": lat, "longitude": lon,
                  "start_date": cur.isoformat(), "end_date": chunk_end.isoformat(),
                  "hourly": ",".join(AIR_MAP), "timezone": "Asia/Kolkata"}
        try:
            frames.append(pd.DataFrame(get_json(AIR_URL, params)["hourly"]))
        except requests.HTTPError as e:
            print(f"  skipped {cur} to {chunk_end}: {e}")
        cur = chunk_end + timedelta(days=1)
        time.sleep(1)
    if not frames:
        return pd.DataFrame(columns=["time"] + list(AIR_MAP.values()))
    return pd.concat(frames, ignore_index=True).rename(columns=AIR_MAP)

raw = Path(BASE) / "raw_data"; raw.mkdir(exist_ok=True)
weather_all, air_all = [], []

for city, (lat, lon, region) in CITIES.items():
    print(f"Fetching {city}...")
    w = fetch_weather_daily(lat, lon)
    w.insert(0, "city", city); w.insert(1, "region", region)
    weather_all.append(w)
    time.sleep(1)

    a = fetch_air_hourly(lat, lon)
    a.insert(0, "city", city); a.insert(1, "region", region)
    air_all.append(a)

weather_df = pd.concat(weather_all, ignore_index=True)
air_df = pd.concat(air_all, ignore_index=True)

weather_df.to_csv(raw / "weather_daily_raw.csv", index=False)
air_df.to_csv(raw / "air_hourly_raw.csv", index=False)

print("Weather:", weather_df.shape)
print("Air:", air_df.shape)
print(air_df.groupby("city").size())