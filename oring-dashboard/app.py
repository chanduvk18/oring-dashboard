import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- CONFIGURATION ---
# Replace with your Published Google Sheet CSV URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpPtnbWx6ktWSLKZguqumjJx86uTpTDxE5edOj95WWUWDcGrG2gOxY6avxeOxJGgR0n3FisNE0jWOF/pub?gid=0&single=true&output=csv"

# Industrial thresholds for maintenance alerts
THRESHOLD_FLASHES = 50   
THRESHOLD_CRACKS = 20    

st.set_page_config(page_title="O-Ring Smart Maintenance", layout="wide")

@st.cache_data(ttl=2) # Check for new data every 2 seconds
def get_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        return df
    except:
        return pd.DataFrame()

df_raw = get_data()

# --- INITIALIZE RESET STATE ---
# This tracks if the user has "reset" the maintenance count for the current session
if 'reset_count' not in st.session_state:
    st.session_state.reset_count = 0

# --- HEADER & SIDEBAR ---
st.title("🏭 Smart Maintenance & Quality Dashboard")
st.sidebar.header("Control Panel")

# 1. THE RESET BUTTON
if st.sidebar.button("🛠️ Mark Maintenance as Complete"):
    # This logic "zeros out" the counters for the UI without deleting history
    st.session_state.reset_count = len(df_raw) 
    st.sidebar.success("Maintenance log reset!")

time_filter = st.sidebar.selectbox("History View", ["All Time", "Today", "Last 5 Days"])

# --- DATA FILTERING ---
df = df_raw.copy()
now = datetime.now()

if time_filter == "Today":
    df = df[df['Timestamp'].dt.date == now.date()]
elif time_filter == "Last 5 Days":
    df = df[df['Timestamp'] > (now - timedelta(days=5))]

# --- MAINTENANCE LOGIC ---
if not df.empty:
    # Adjust count based on the Reset button action
    current_session_df = df_raw.iloc[st.session_state.reset_count:]
    
    flash_count = len(current_session_df[current_session_df['Defect_Type'] == 'FLASHES'])
    crack_count = len(current_session_df[current_session_df['Defect_Type'] == 'CRACK'])

    st.subheader("🛠️ Machine Health Status")
    status_col1, status_col2 = st.columns(2)

    with status_col1:
        if flash_count >= THRESHOLD_FLASHES:
            st.error(f"🚨 CRITICAL: REPLACE TRIMMING BLADE ({flash_count}/{THRESHOLD_FLASHES})")
        else:
            st.success(f"✅ Trimming Blade Condition: GOOD ({flash_count}/{THRESHOLD_FLASHES})")

    with status_col2:
        if crack_count >= THRESHOLD_CRACKS:
            st.warning(f"⚠️ ATTENTION: INSPECT HEATING UNIT ({crack_count}/{THRESHOLD_CRACKS})")
        else:
            st.success(f"✅ Material Quality: STABLE ({crack_count}/{THRESHOLD_CRACKS})")

    st.divider()

    # --- KPI & CHARTS ---
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Detections (History)", len(df))
    m2.metric("Current Session Defects", len(current_session_df))
    m3.metric("Last Fault Detected", df['Timestamp'].max().strftime('%H:%M:%S'))

    c1, c2 = st.columns(2)
    with c1:
        fig_bar = px.bar(df['Defect_Type'].value_counts().reset_index(), x='index', y='Defect_Type', 
                         title="Defect Distribution (All History)", template="plotly_dark")
        st.plotly_chart(fig_bar, use_container_width=True)
    with c2:
        # Timeline of all detected faults
        df_time = df.set_index('Timestamp').resample('H').count().reset_index()
        fig_line = px.line(df_time, x='Timestamp', y='Defect_Type', title="Defect Trend Line", template="plotly_dark")
        st.plotly_chart(fig_line, use_container_width=True)
else:
    st.warning("No data found in Google Sheet. Check if Raspberry Pi has sent any detections.")
