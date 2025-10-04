import streamlit as st
import pandas as pd
import joblib
import altair as alt
import pydeck as pdk
import os
import hashlib


# Utility: Password Hashing

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


# Load Model + Encoder

model = joblib.load("aqi_predictor_with_pm.pkl")
le = joblib.load("label_encoder.pkl")


# User Database Setup

USER_FILE = "users.csv"
if not os.path.exists(USER_FILE):
    df_users = pd.DataFrame([{"username": "admin", "password": hash_password("1234")}])
    df_users.to_csv(USER_FILE, index=False)


# Helper Functions

def signup(username, password):
    users = pd.read_csv(USER_FILE)
    if username in users["username"].values:
        return False, "⚠️ Username already exists!"
    else:
        users = pd.concat(
            [users, pd.DataFrame([[username, hash_password(password)]], columns=["username", "password"])],
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


# AQI Categories & Recommendations

AQI_RANGES = {
    "Good": (0, 50),
    "Moderate": (51, 100),
    "Unhealthy for Sensitive": (101, 150),
    "Unhealthy": (151, 200),
    "Very Unhealthy": (201, 300),
    "Hazardous": (301, 500),
}

RECOMMENDATIONS = {
    "Good": ["Air quality is satisfactory; no precautions needed.", "Encourage outdoor activities."],
    "Moderate": ["Air quality is acceptable, but sensitive groups may be affected.",
                 "Children, elderly, and asthma patients should reduce heavy outdoor activity."],
    "Unhealthy for Sensitive": ["Sensitive people should wear masks outdoors.",
                                "Schools should reduce outdoor sports activities."],
    "Unhealthy": ["Everyone may begin to experience health effects.",
                  "Avoid jogging or cycling outdoors.",
                  "Use air purifiers indoors."],
    "Very Unhealthy": ["Serious health risk; avoid outdoor activities.",
                       "Hospitals should prepare for more respiratory cases."],
    "Hazardous": ["Emergency conditions; entire population affected.",
                  "Government advisories: close schools and offices if necessary."]
}


# Session State Init

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None


# Login / Signup Page

if not st.session_state.logged_in:
    st.title("🔐 User Authentication")
    tab1, tab2 = st.tabs(["Login", "Signup"])

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


# AQI Prediction App (After Login)

else:
    # ---- CSS Styling ----
    st.markdown(
        """
        <style>
        .stApp { background-color: #ffffff; color: #333333; }
        section[data-testid="stSidebar"] { background-color: #2c2f38; }
        section[data-testid="stSidebar"] * { color: #ffffff; }
        .block-container { max-width: 95%; padding-left: 2rem; padding-right: 2rem; }
        </style>
        """, unsafe_allow_html=True
    )

    st.sidebar.success(f"Welcome {st.session_state.user} 👋")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

    st.title("🌍 Air Quality Index (AQI) Prediction Dashboard")
    st.markdown("This tool predicts **AQI Category** based on pollutant and weather measurements.")

    tab1, tab2 = st.tabs(["🔮 Single Prediction", "📂 Batch Prediction"])

    
    # SINGLE PREDICTION
   
    with tab1:
        st.sidebar.header("🔧 Input Parameters")
        pm25 = st.sidebar.number_input("PM2.5 (µg/m³)", 0.0, 500.0, 0.1)
        pm10 = st.sidebar.number_input("PM10 (µg/m³)", 0.0, 600.0, 0.1)
        no2 = st.sidebar.number_input("NO₂ (µg/m³)", 0.0, 400.0, 0.1)
        co = st.sidebar.number_input("CO (mg/m³)", 0.0, 50.0, 0.1)
        temp_c = st.sidebar.number_input("Temperature (°C)", -20.0, 60.0, 0.1)
        lon = st.sidebar.number_input("Longitude", -180.0, 180.0, 0.1)
        lat = st.sidebar.number_input("Latitude", -90.0, 90.0, 0.1)

        if st.sidebar.button("🔮 Predict AQI Category"):
            X_new = pd.DataFrame([[pm25, pm10, lon, lat, no2, co, temp_c]],
                                 columns=['pm25','pm10','lon','lat','no2','co','temp_c'])

            pred = model.predict(X_new)
            probs = model.predict_proba(X_new)[0]
            category = le.inverse_transform(pred)[0]
            cat_range = AQI_RANGES.get(category, (0,0))

            st.markdown(f"### ✅ Predicted Category: **{category}**")
            st.markdown(f"**AQI Range for {category}: {cat_range[0]}–{cat_range[1]}**")
            st.markdown("### 🛠 Recommendations")
            for rec in RECOMMENDATIONS[category]:
                st.write(f"- {rec}")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("### 📊 Prediction Probabilities")
                prob_df = pd.DataFrame({"Category": le.classes_, "Probability": probs})
                st.altair_chart(
                    alt.Chart(prob_df).mark_bar().encode(
                        x=alt.X("Category:N", sort=le.classes_, title="AQI Category"),
                        y=alt.Y("Probability:Q", title="Prediction Probability", scale=alt.Scale(domain=[0,1])),
                        color=alt.value("#1f77b4")
                    ).properties(width=350, height=350), use_container_width=True)

            with col2:
                st.markdown("### 📊 Pollutant Levels vs WHO Guidelines")
                safe_limits = {"pm25": 25, "pm10": 50, "no2": 40, "co": 10}
                comp_df = pd.DataFrame({
                    "Pollutant": list(safe_limits.keys()),
                    "Input Value": [pm25, pm10, no2, co],
                    "Safe Limit": list(safe_limits.values())
                })
                st.altair_chart(
                    alt.Chart(comp_df).transform_fold(
                        ["Input Value", "Safe Limit"], as_=["Type", "Value"]
                    ).mark_bar().encode(
                        x=alt.X("Pollutant:N"),
                        y=alt.Y("Value:Q"),
                        color="Type:N"
                    ).properties(width=350, height=350), use_container_width=True)

            with col3:
                st.markdown("### 🌍 Location of Input Coordinates")
                map_df = pd.DataFrame({"lat": [lat], "lon": [lon]})
                view_state = pdk.ViewState(latitude=lat, longitude=lon, zoom=6, pitch=0)
                layer = pdk.Layer("ScatterplotLayer", data=map_df,
                                  get_position='[lon, lat]', get_color='[200, 30, 0, 160]', get_radius=40000)
                r = pdk.Deck(layers=[layer], initial_view_state=view_state,
                             tooltip={"text": "📍 {lat}, {lon}"})
                st.pydeck_chart(r, use_container_width=True, height=350)

   
    # BATCH PREDICTION
    
    with tab2:
        st.subheader("📂 Upload CSV/XLSX for Batch Prediction")
        uploaded = st.file_uploader("Upload file", type=["csv", "xlsx"])
        if uploaded:
            data = pd.read_csv(uploaded) if uploaded.name.endswith(".csv") else pd.read_excel(uploaded)
            st.dataframe(data.head())
            preds = model.predict(data)
            categories = le.inverse_transform(preds)
            results = data.copy()
            results["Predicted_AQI_Category"] = categories
            results["Explanation"] = results["Predicted_AQI_Category"].apply(
                lambda c: f"AQI falls in {c} range {AQI_RANGES.get(c,(0,0))}"
            )
            results["Recommendations"] = results["Predicted_AQI_Category"].apply(
                lambda c: " | ".join(RECOMMENDATIONS[c])
            )
            st.dataframe(results.head())
            st.download_button("📥 Download Results", results.to_csv(index=False), "aqi_batch_results.csv", "text/csv")
