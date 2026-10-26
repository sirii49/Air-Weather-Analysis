import pandas as pd

# 1. Load the raw files
weather = pd.read_csv("weather_daily.csv", parse_dates=["time"])
air = pd.read_csv("air_hourly.csv", parse_dates=["time"])

# 2. Hourly air data -> daily average
air["time"] = air["time"].dt.date
weather["time"] = weather["time"].dt.date
air_daily = air.groupby(["city", "region", "time"]).mean().reset_index()

# 3. Join weather and air data
df = weather.merge(air_daily, on=["city", "region", "time"])

# 4. Remove rows with missing values
df = df.dropna()

# 5. Remove impossible values
df = df[(df["humidity"] <= 100) & (df["pm25"] >= 0) & (df["aqi"] <= 500)]

# 6. Add new columns
df["time"] = pd.to_datetime(df["time"])
df["month"] = df["time"].dt.month
df["is_weekend"] = (df["time"].dt.dayofweek >= 5).astype(int)

def get_season(m):
    if m in [12, 1, 2]:
        return "Winter"
    elif m in [3, 4, 5]:
        return "Summer"
    elif m in [6, 7, 8, 9]:
        return "Monsoon"
    else:
        return "Post-monsoon"

df["season"] = df["month"].apply(get_season)

df["aqi_category"] = pd.cut(df["aqi"],
                            bins=[-1, 50, 100, 150, 200, 300, 500],
                            labels=["Good", "Moderate", "Unhealthy for Sensitive",
                                    "Unhealthy", "Very Unhealthy", "Hazardous"])

# 7. Pollutant as % of safe limit
df["pm25_pct"] = df["pm25"] / 60 * 100
df["pm10_pct"] = df["pm10"] / 100 * 100
df["no2_pct"] = df["no2"] / 80 * 100
df["so2_pct"] = df["so2"] / 80 * 100
df["o3_pct"] = df["o3"] / 100 * 100
df["co_pct"] = df["co"] / 2000 * 100

# 8. Round to 2 decimals and save
df = df.round(2)
df.to_csv("cleaned_data.csv", index=False)
print(df.shape)
print(df.groupby("city").size())