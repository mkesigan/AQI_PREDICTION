import pandas as pd

# Load dataset
df = pd.read_csv("waqi_global_dataset_timeseries.csv")

# Ensure AQI numeric
df["aqi"] = pd.to_numeric(df["aqi"], errors="coerce")

# AQI Category function
def aqi_to_category(aqi):
    if pd.isna(aqi):
        return "Unknown"
    elif aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"

df["aqi_category"] = df["aqi"].apply(aqi_to_category)

# Convert time column to datetime
df["time"] = pd.to_datetime(df["time"], errors="coerce")

# Season from month
df["month"] = df["time"].dt.month
def month_to_season(m):
    if pd.isna(m):
        return "Unknown"
    if m in [12,1,2]: return "Winter"
    elif m in [3,4,5]: return "Spring"
    elif m in [6,7,8]: return "Summer"
    else: return "Autumn"
df["season"] = df["month"].apply(month_to_season)

# Temperature condition
df["temp_c"] = pd.to_numeric(df.get("temp_c"), errors="coerce")
def temp_to_condition(t):
    if pd.isna(t): return "Unknown"
    if t < 10: return "Cold"
    elif t < 25: return "Mild"
    else: return "Hot"
df["temp_condition"] = df["temp_c"].apply(temp_to_condition)

# Save new dataset
df.to_csv("waqi_global_dataset_with_categoricals.csv", index=False)

print("✅ Saved waqi_global_dataset_with_categoricals.csv")
print(df[["aqi","aqi_category","season","temp_c","temp_condition"]].head(10))
