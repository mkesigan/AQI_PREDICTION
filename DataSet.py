# waqi_collect_until_10k.py
import os, time, requests, pandas as pd

WAQI_TOKEN = os.getenv("WAQI_TOKEN", "ac3baf8cb4ba2298d3bd1a0cc9bdd4057cf6fafc")
OUT_CSV = "waqi_global_dataset_timeseries.csv"

# sleep between station feed requests (be polite to API)
SLEEP_FEED = 0.35
# sleep between rounds (minutes). Lower is faster, higher is safer.
SLEEP_BETWEEN_ROUNDS_MIN = 5
TARGET_RECORDS = 12000

BASE = "https://api.waqi.info"

# Small world-coverage grid of bounds (tune if needed)
TILES = []
for s in range(-60, 61, 20):      # latitude bands
    for w in range(-180, 181, 30): # longitude bands
        TILES.append((s, w, s+20, w+30))

def waqi_get(url, params=None):
    params = params or {}
    params["token"] = WAQI_TOKEN
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    if data.get("status") != "ok":
        raise RuntimeError(f"WAQI API status not ok: {data}")
    return data

def list_stations():
    seen, stations = set(), []
    for (south, west, north, east) in TILES:
        try:
            data = waqi_get(f"{BASE}/map/bounds/", {"latlng": f"{south},{west},{north},{east}"})
            for st in data.get("data", []):
                uid = st.get("uid")
                if uid and uid not in seen:
                    seen.add(uid)
                    stations.append(uid)
        except Exception as e:
            print(f"[bounds] {south},{west},{north},{east} -> {e}")
        time.sleep(0.25)
    print(f"Discovered {len(stations)} unique stations")
    return stations

def fetch_station(uid):
    try:
        d = waqi_get(f"{BASE}/feed/@{uid}/").get("data", {})
    except Exception as e:
        return None
    city = (d.get("city") or {})
    iaqi = d.get("iaqi") or {}
    def v(k): return (iaqi.get(k) or {}).get("v")
    row = {
        "uid": uid,
        "time": (d.get("time") or {}).get("s"),
        "aqi": d.get("aqi"),
        "city_name": city.get("name"),
        "lat": (city.get("geo") or [None, None])[0],
        "lon": (city.get("geo") or [None, None])[1],
        "pm25": v("pm25"), "pm10": v("pm10"),
        "no2": v("no2"), "so2": v("so2"),
        "co": v("co"), "o3": v("o3"),
        "temp_c": v("t"), "humidity_pct": v("h"),
        "pressure_hpa": v("p"), "wind_speed_mps": v("w")
    }
    return row

def load_existing():
    if not os.path.exists(OUT_CSV): return pd.DataFrame()
    try:
        return pd.read_csv(OUT_CSV)
    except Exception:
        return pd.DataFrame()

def save_append(df_new):
    df_old = load_existing()
    df = pd.concat([df_old, df_new], ignore_index=True)
    # dedup on (uid, time)
    if "uid" in df.columns and "time" in df.columns:
        df.drop_duplicates(subset=["uid","time"], inplace=True)
    df.to_csv(OUT_CSV, index=False)
    return len(df)

def main():
    assert WAQI_TOKEN and WAQI_TOKEN != "PUT_YOUR_TOKEN_HERE", "Set WAQI_TOKEN first."
    stations = list_stations()
    total = len(load_existing())
    print(f"Starting with {total} rows in {OUT_CSV} (if any)")

    round_idx = 0
    while total < TARGET_RECORDS:
        round_idx += 1
        print(f"\n=== Round {round_idx} ===")
        rows = []
        for i, uid in enumerate(stations, 1):
            row = fetch_station(uid)
            if row and row.get("time"):
                rows.append(row)
            if i % 100 == 0:
                print(f"  fetched {i}/{len(stations)} stations")
            time.sleep(SLEEP_FEED)
        if not rows:
            print("No rows fetched this round.")
        df_new = pd.DataFrame(rows)
        total = save_append(df_new)
        print(f"Round {round_idx}: added {len(df_new)} rows. Total now: {total}")

        if total >= TARGET_RECORDS:
            break
        print(f"Sleeping {SLEEP_BETWEEN_ROUNDS_MIN} min before next round...")
        time.sleep(SLEEP_BETWEEN_ROUNDS_MIN * 60)

    print(f"Done. {OUT_CSV} has {total} unique rows (uid,time).")

if __name__ == "__main__":
    main()
