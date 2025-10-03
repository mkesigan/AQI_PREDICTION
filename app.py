import streamlit as st
import pandas as pd
import joblib
import altair as alt
import pydeck as pdk
import os
import hashlib

# =========================
# Utility: Password Hashing
# =========================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# =========================
# Load Model + Encoder
# =========================
model = joblib.load("aqi_predictor_with_pm.pkl")
le = joblib.load("label_encoder.pkl")

# =========================
# User Database Setup
# =========================
USER_FILE = "users.csv"

# Create user file if not exists
if not os.path.exists(USER_FILE):
    df_users = pd.DataFrame(
        [{"username": "admin", "password": hash_password("1234")}]
    )
    df_users.to_csv(USER_FILE, index=False)

# =========================
# Helper Functions
# =========================
def signup(username, password):
    users = pd.read_csv(USER_FILE)
    if username in users["username"].values:
        return False, "⚠️ Username already exists!"
    else:
        users = pd.concat(
            [users, pd.DataFrame([[username, hash_password(password)]], 
                                 columns=["username", "password"])],
            ignore_index=True
        )
        users.to_csv(USER_FILE, index=False)
        return True, "✅ Signup successful! Please login."

def login(username, password):
    users = pd.read_csv(USER_FILE)
    if username in users["username"].values:
        stored_pass = users.loc[users["username"] == username, "password"].values[0]
        if stored_pass == hash_password(password):
            return True, "✅ Login successful!"
        else:
            return False, "❌ Incorrect password."
    else:
        return False, "❌ Username not found."

# =========================
# Session State Init
# =========================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None

# =========================
# Login / Signup Page
# =========================
if not st.session_state.logged_in:
    st.title("🔐 User Authentication")

    tab1, tab2 = st.tabs(["Login", "Signup"])

    # ---- Login ----
    with tab1:
        st.subheader("Login")
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            success, msg = login(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.user = username
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    # ---- Signup ----
    with tab2:
        st.subheader("Signup")
        new_user = st.text_input("Create Username", key="signup_user")
        new_pass = st.text_input("Create Password", type="password", key="signup_pass")
        if st.button("Signup"):
            success, msg = signup(new_user, new_pass)
            if success:
                st.success(msg)
            else:
                st.error(msg)

# =========================
# AQI Prediction App (After Login)
# =========================
else:
    # ---- CSS Styling ----
    st.markdown(
        """
        <style>
        /* Main page background */
        .stApp {
            background-color: #ffffff; /* white */
            color: #333333;
        }
        /* Sidebar background */
        section[data-testid="stSidebar"] {
            background-color: #2c2f38;
        }
        section[data-testid="stSidebar"] * {
            color: #ffffff;
        }
        /* Center containers */
        .block-container {
            max-width: 95%;
            padding-left: 2rem;
            padding-right: 2rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # ---- Sidebar ----
    st.sidebar.success(f"Welcome {st.session_state.user} 👋")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

    st.sidebar.header("🔧 Input Parameters")
    pm25 = st.sidebar.number_input("PM2.5 (µg/m³)", min_value=0.0, max_value=500.0, step=0.1)
    pm10 = st.sidebar.number_input("PM10 (µg/m³)", min_value=0.0, max_value=600.0, step=0.1)
    no2  = st.sidebar.number_input("NO₂ (µg/m³)", min_value=0.0, max_value=400.0, step=0.1)
    co   = st.sidebar.number_input("CO (mg/m³)", min_value=0.0, max_value=50.0, step=0.1)
    temp_c = st.sidebar.number_input("Temperature (°C)", min_value=-20.0, max_value=60.0, step=0.1)
    lon  = st.sidebar.number_input("Longitude", min_value=-180.0, max_value=180.0, step=0.1)
    lat  = st.sidebar.number_input("Latitude", min_value=-90.0, max_value=90.0, step=0.1)

    # ---- Main Page ----
    st.title("🌍 Air Quality Index (AQI) Prediction Dashboard")
    st.markdown("This tool predicts **AQI Category** based on pollutant and weather measurements.")

    if st.sidebar.button("🔮 Predict AQI Category"):
        X_new = pd.DataFrame([[pm25, pm10, lon, lat, no2, co, temp_c]],
                             columns=['pm25','pm10','lon','lat','no2','co','temp_c'])

        pred = model.predict(X_new)
        probs = model.predict_proba(X_new)[0]
        category = le.inverse_transform(pred)[0]

        color_map = {
            "Good": "🟢",
            "Moderate": "🟡",
            "Unhealthy for Sensitive": "🟠",
            "Unhealthy": "🔴",
            "Very Unhealthy": "🟣",
            "Hazardous": "⚫",
            "Unknown": "⚪"
        }
        st.markdown(f"## {color_map.get(category, '❓')} **{category}**")

        col1, col2, col3 = st.columns(3)

        # --- Probabilities ---
        with col1:
            st.markdown("### 📊 Model Prediction Probabilities")
            prob_df = pd.DataFrame({"Category": le.classes_, "Probability": probs})
            prob_chart = alt.Chart(prob_df).mark_bar().encode(
                x=alt.X("Category:N", sort=le.classes_, title="AQI Category"),
                y=alt.Y("Probability:Q", title="Prediction Probability", scale=alt.Scale(domain=[0,1])),
                color=alt.value("#1f77b4")
            ).properties(width=350, height=350)
            st.altair_chart(prob_chart, use_container_width=True)

        # --- Pollutant Comparison ---
        with col2:
            st.markdown("### 📊 Pollutant Levels vs WHO Guidelines")
            safe_limits = {"pm25": 25, "pm10": 50, "no2": 40, "co": 10}
            input_vals = {"pm25": pm25, "pm10": pm10, "no2": no2, "co": co}
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
            ).properties(width=350, height=350)
            st.altair_chart(comp_chart, use_container_width=True)

        # --- Location Map ---
        with col3:
            st.markdown("### 🌍 Location of Input Coordinates")
            map_df = pd.DataFrame({"lat": [lat], "lon": [lon]})
            view_state = pdk.ViewState(latitude=lat, longitude=lon, zoom=6, pitch=0)
            layer = pdk.Layer("ScatterplotLayer", data=map_df,
                              get_position='[lon, lat]',
                              get_color='[200, 30, 0, 160]',
                              get_radius=40000)
            r = pdk.Deck(layers=[layer], initial_view_state=view_state,
                         tooltip={"text": "📍 Location: {lat}, {lon}"})
            st.pydeck_chart(r, use_container_width=True, height=350)
