import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

# --- CONFIGURATION ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vSpPtnbWx6ktWSLKZguqumjJx86uTpTDxE5edOj95WWUWDcGrG2gOxY6avxeOxJGgR0n3FisNE0jWOF/pub?gid=0&single=true&output=csv"
THRESHOLD_FLASHES = 50   
THRESHOLD_CRACKS = 20    

st.set_page_config(page_title="O-Ring Smart Maintenance", layout="wide")

@st.cache_data(ttl=2)
def get_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        return df
    except:
        return pd.DataFrame()

df_raw = get_data()

# --- SIDEBAR & LOGIC ---
st.sidebar.header("Control Panel")
if 'reset_count' not in st.session_state:
    st.session_state.reset_count = 0

if st.sidebar.button("🛠️ Mark Maintenance as Complete"):
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

# --- TIME BINNING LOGIC (The 6 Bars) ---
# We define 6 bins: 6-8am, 8-10am, 10-12pm, 12-2pm, 2-4pm, 4-6pm
bins = [6, 8, 10, 12, 14, 16, 18]
labels = ["6-8 AM", "8-10 AM", "10-12 PM", "12-2 PM", "2-4 PM", "4-6 PM"]

if not df.empty:
    # Extract hour and assign to bin
    df['Hour'] = df['Timestamp'].dt.hour
    df['Time_Slot'] = pd.cut(df['Hour'], bins=bins, labels=labels, right=False)
    
    # Machine Health logic (as before)
    current_session_df = df_raw.iloc[st.session_state.reset_count:]
    flash_count = len(current_session_df[current_session_df['Defect_Type'] == 'FLASHES'])
    crack_count = len(current_session_df[current_session_df['Defect_Type'] == 'CRACK'])

    st.title("🏭 O-Ring Smart Maintenance Dashboard")
    
    # --- MAINTENANCE STATUS ---
    s1, s2 = st.columns(2)
    with s1:
        if flash_count >= THRESHOLD_FLASHES: st.error(f"🚨 REPLACE BLADE ({flash_count}/{THRESHOLD_FLASHES})")
        else: st.success(f"✅ Blade Condition: GOOD ({flash_count}/{THRESHOLD_FLASHES})")
    with s2:
        if crack_count >= THRESHOLD_CRACKS: st.warning(f"⚠️ INSPECT HEAT ({crack_count}/{THRESHOLD_CRACKS})")
        else: st.success(f"✅ Material: STABLE ({crack_count}/{THRESHOLD_CRACKS})")

    st.divider()

    # --- ROW 1: PIE CHART & TOTAL BAR CHART ---
    row1_col1, row1_col2 = st.columns(2)
    
    with row1_col1:
        st.subheader("Defect Percentage (Pie)")
        fig_pie = px.pie(df, names='Defect_Type', hole=0.4, template="plotly_dark",
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_pie, use_container_width=True)

    with row1_col2:
        st.subheader("Total Defects (All Types)")
        total_binned = df['Time_Slot'].value_counts().reindex(labels).reset_index()
        fig_total = px.bar(total_binned, x='index', y='Time_Slot', labels={'Time_Slot':'Count', 'index':'Time Slot'},
                           template="plotly_dark", color_discrete_sequence=['#3498db'])
        st.plotly_chart(fig_total, use_container_width=True)

    # --- ROW 2: SPECIFIC DEFECT BAR CHARTS ---
    st.divider()
    st.subheader("Defect Specific Hourly Analysis")
    b1, b2, b3 = st.columns(3)

    # Helper function to create the specific bar charts
    def create_defect_chart(defect_name, color):
        defect_df = df[df['Defect_Type'] == defect_name]
        binned = defect_df['Time_Slot'].value_counts().reindex(labels).reset_index()
        fig = px.bar(binned, x='index', y='Time_Slot', title=f"{defect_name} Distribution",
                     labels={'Time_Slot':'Count', 'index':'Time Slot'},
                     template="plotly_dark", color_discrete_sequence=[color])
        return fig

    with b1:
        st.plotly_chart(create_defect_chart('FLASHES', '#f1c40f'), use_container_width=True)
    with b2:
        st.plotly_chart(create_defect_chart('CRACK', '#e67e22'), use_container_width=True)
    with b3:
        st.plotly_chart(create_defect_chart('BREAKAGE', '#e74c3c'), use_container_width=True)

else:
    st.warning("Awaiting live data from Raspberry Pi...")


