import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Page Config
st.set_page_config(page_title="O-Ring Quality Dashboard", layout="wide")
st.title("🏭 Industrial O-Ring Inspection Analytics")

# 2. Connect to Data (Replace with your Sheet CSV link)
# Tip: In Google Sheets, File > Share > Publish to Web > Select Sheet 1 as CSV
SHEET_CSV_URL = "https://script.google.com/macros/s/AKfycbzNtMghS_xCZcZvJpEfYBLZnnjQwgzQNH48Wo52vRYkFOmD1T3k6unH4Bk2k8BmT_64FQ/exec"

@st.cache_data(ttl=10) # Refresh data every 10 seconds
def load_data():
    df = pd.read_csv(SHEET_CSV_URL)
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    return df

try:
    data = load_data()

    # 3. Sidebar Filter
    st.sidebar.header("Filter Data")
    days = st.sidebar.selectbox("Select Time Range", ["Today", "Last 5 Days", "All Time"])
    
    # Filter Logic
    if days == "Today":
        data = data[data['Timestamp'].dt.date == pd.Timestamp.now().date()]
    elif days == "Last 5 Days":
        data = data[data['Timestamp'] > (pd.Timestamp.now() - pd.Timedelta(days=5))]

    # 4. KPI Tiles
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Defects", len(data))
    col2.metric("Most Common", data['Defect_Type'].mode()[0] if not data.empty else "N/A")
    col3.metric("Avg Confidence", f"{data['Confidence'].mean():.2f}")

    # 5. Charts
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("Defect Distribution (Bar Chart)")
        fig_bar = px.histogram(data, x="Defect_Type", color="Defect_Type", 
                              template="plotly_dark")
        st.plotly_chart(fig_bar, use_container_width=True)

    with chart_col2:
        st.subheader("Defects Over Time (Line Chart)")
        # Group by hour/minute for the timeline
        timeline = data.resample('H', on='Timestamp').count().reset_index()
        fig_line = px.line(timeline, x="Timestamp", y="Defect_Type", 
                          labels={'Defect_Type': 'Count'}, template="plotly_dark")
        st.plotly_chart(fig_line, use_container_width=True)

except:
    st.warning("Waiting for data from Raspberry Pi... Make sure the Google Sheet is published to web as CSV.")
