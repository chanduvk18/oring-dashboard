import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- CONFIGURATION ---
# Replace with your Published Google Sheet CSV URL
SHEET_URL = "YOUR_GOOGLE_SHEET_CSV_URL_HERE"

# Define your industrial thresholds for maintenance
THRESHOLD_FLASHES = 50   # If > 50 flashes, blade is dull
THRESHOLD_CRACKS = 20    # If > 20 cracks, raw material/heat is bad

st.set_page_config(page_title="O-Ring Smart Maintenance", layout="wide")

@st.cache_data(ttl=5)
def get_data():
    df = pd.read_csv(SHEET_URL)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df

try:
    df = get_data()

    # --- HEADER & MAINTENANCE STATUS ---
    st.title("🏭 Smart Maintenance & Quality Dashboard")
    
    # Calculate current counts
    flash_count = len(df[df['Defect_Type'] == 'FLASHES'])
    crack_count = len(df[df['Defect_Type'] == 'CRACK'])

    # Maintenance Logic
    st.subheader("🛠️ Machine Health Status")
    status_col1, status_col2 = st.columns(2)

    with status_col1:
        if flash_count >= THRESHOLD_FLASHES:
            st.error(f"🚨 CRITICAL: TRIMMING BLADE REPLACEMENT REQUIRED ({flash_count}/{THRESHOLD_FLASHES} Flashes)")
        else:
            st.success(f"✅ Trimming Blade Condition: GOOD ({flash_count}/{THRESHOLD_FLASHES})")

    with status_col2:
        if crack_count >= THRESHOLD_CRACKS:
            st.warning(f"⚠️ ATTENTION: INSPECT HEATING UNIT / RAW MATERIAL ({crack_count}/{THRESHOLD_CRACKS} Cracks)")
        else:
            st.success(f"✅ Material Quality: STABLE ({crack_count}/{THRESHOLD_CRACKS})")

    st.divider()

    # --- KPI & CHARTS ---
    # (Existing KPI and Chart code goes here)
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Defects", len(df))
    m2.metric("System Uptime", "99.8%")
    m3.metric("Last Sync", df['Timestamp'].max().strftime('%H:%M:%S'))

    # Visualizing the Maintenance Limit
    st.subheader("Maintenance Threshold Tracking")
    limit_data = pd.DataFrame({
        'Defect': ['FLASHES', 'CRACK'],
        'Current': [flash_count, crack_count],
        'Limit': [THRESHOLD_FLASHES, THRESHOLD_CRACKS]
    })
    fig_limit = px.bar(limit_data, x='Defect', y=['Current', 'Limit'], 
                       barmode='group', template="plotly_dark",
                       color_discrete_map={'Current': '#3498db', 'Limit': '#e74c3c'})
    st.plotly_chart(fig_limit, use_container_width=True)

except Exception as e:
    st.info("Awaiting live data from Raspberry Pi...")


