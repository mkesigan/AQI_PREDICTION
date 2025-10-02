# 🌍 Air Quality Index (AQI) Prediction

This project predicts **AQI Categories** (Good, Moderate, Unhealthy, etc.) using machine learning on WAQI datasets and provides a **Streamlit dashboard**.

## 🚀 Features
- Data preprocessing (missing values, duplicates, outliers handling)
- Model training with Logistic Regression, Random Forest, Gradient Boosting
- Model selection based on accuracy & performance
- Frontend dashboard (Streamlit) with:
  - AQI prediction
  - Model probability visualization
  - Pollutant vs WHO guidelines chart
  - Map visualization of input coordinates
- Authentication (login/signup)

## 📂 Repository Structure
(Explain the folders like shown above)

## ⚡ How to Run
```bash
# Clone repo
git clone https://github.com/mkesigan/AQI_PREDICTION
cd AQI_PREDICTION

# Install dependencies
pip install -r requirements.txt

# Run Streamlit app
streamlit run app/app.py
