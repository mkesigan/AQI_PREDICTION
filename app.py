import streamlit as st
import pandas as pd
import joblib
import altair as alt

# -------------------------
# Load Model + Encoder
# -------------------------
model = joblib.load("aqi_predictor_with_pm.pkl")
le = joblib.load("label_encoder.pkl")

# -------------------------
# Page Config
# -------------------------
st.set_page_config(page_title="🌍 AQI Prediction Dashboard",
                   page_icon="🌱",
                   layout="wide")

# ---- Custom CSS for background ----
st.markdown(
    """
    <style>
    .stApp {
        background-color: #f5f5f5; /* light ash */
        color: #333333;  /* dark grey text */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# -------------------------
# Title
# -------------------------
st.title("🌍 Air Quality Index (AQI) Prediction Dashboard")
st.markdown("This tool predicts **AQI Category** based on pollutant and weather measurements.")

# -------------------------
# Sidebar Inputs
# -------------------------
st.sidebar.header("🔧 Input Parameters")

pm25 = st.sidebar.number_input("PM2.5 (µg/m³)", min_value=0.0, max_value=500.0, step=0.1)
pm10 = st.sidebar.number_input("PM10 (µg/m³)", min_value=0.0, max_value=600.0, step=0.1)
no2  = st.sidebar.number_input("NO₂ (µg/m³)", min_value=0.0, max_value=400.0, step=0.1)
so2  = st.sidebar.number_input("SO₂ (µg/m³)", min_value=0.0, max_value=400.0, step=0.1)
co   = st.sidebar.number_input("CO (mg/m³)", min_value=0.0, max_value=50.0, step=0.1)
o3   = st.sidebar.number_input("O₃ (µg/m³)", min_value=0.0, max_value=500.0, step=0.1)
pressure = st.sidebar.number_input("Pressure (hPa)", min_value=800.0, max_value=1100.0, step=0.1)
humidity = st.sidebar.number_input("Humidity (%)", min_value=0.0, max_value=100.0, step=0.1)

# -------------------------
# Prediction
# -------------------------
if st.sidebar.button("🔮 Predict AQI Category"):
    X_new = pd.DataFrame([[pm25, pm10, no2, so2, co, o3, pressure, humidity]],
                         columns=["pm25","pm10","no2","so2","co","o3","pressure_hpa","humidity_pct"])

    pred = model.predict(X_new)
    probs = model.predict_proba(X_new)[0]
    category = le.inverse_transform(pred)[0]

    # --- Prediction Category ---
    st.subheader("✅ Predicted AQI Category")
    color_map = {
        "Good": "🟢",
        "Moderate": "🟡",
        "Unhealthy for Sensitive": "🟠",
        "Unhealthy": "🔴",
        "Very Unhealthy": "🟣",
        "Hazardous": "⚫",
        "Unknown": "⚪"
    }
    st.markdown(f"### {color_map.get(category, '❓')} **{category}**")

    # --- Two Column Layout for Graphs ---
    col1, col2 = st.columns([2,2])

    # --- Column 1: Prediction Probabilities ---
    with col1:
        st.markdown("### 📊 Model Prediction Probabilities")  # Title outside
        prob_df = pd.DataFrame({
            "Category": le.classes_,
            "Probability": probs
        })

        prob_chart = alt.Chart(prob_df).mark_bar().encode(
            x=alt.X("Category:N", sort=le.classes_, title="AQI Category"),
            y=alt.Y("Probability:Q", title="Prediction Probability", scale=alt.Scale(domain=[0,1])),
            color=alt.value("#1f77b4")
        ).properties(width=400, height=350)

        st.altair_chart(prob_chart, use_container_width=True)

    # --- Column 2: Pollutant Comparison ---
    with col2:
        st.markdown("### 📊 Pollutant Levels vs WHO Guidelines")  # Title outside
        safe_limits = {
            "pm25": 25,
            "pm10": 50,
            "no2": 40,
            "so2": 20,
            "co": 10,
            "o3": 100,
        }
        input_vals = {"pm25": pm25, "pm10": pm10, "no2": no2, "so2": so2, "co": co, "o3": o3}
        comp_df = pd.DataFrame({
            "Pollutant": list(input_vals.keys()),
            "Input Value": list(input_vals.values()),
            "Safe Limit": [safe_limits[p] for p in input_vals.keys()]
        })

        comp_chart = alt.Chart(comp_df).transform_fold(
            ["Input Value", "Safe Limit"],
            as_=["Type", "Value"]
        ).mark_bar().encode(
            x=alt.X("Pollutant:N", title="Pollutants"),
            y=alt.Y("Value:Q", title="Concentration (µg/m³ or mg/m³)"),
            color="Type:N"
        ).properties(width=400, height=350)

        st.altair_chart(comp_chart, use_container_width=True)
