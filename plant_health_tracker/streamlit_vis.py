import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from plant_health_tracker.mock.plant_data import PLANT_MOCK_A, PLANT_MOCK_B #issues importing data
from plant_health_tracker.mock.sensor_data import SENSOR_DATA_MOCK_A, SENSOR_DATA_MOCK_B, MockSensorDataDB
from plant_health_tracker.utils.moisture_evaluation import evaluate_moisture

st.set_page_config(page_title="Plant Health Dashboard", layout="centered")
st.title("🌵 Plant Health Dashboard 🌱")

# Create a dictionary of available plants
PLANTS = {
    PLANT_MOCK_A.name: (PLANT_MOCK_A, SENSOR_DATA_MOCK_A),
    PLANT_MOCK_B.name: (PLANT_MOCK_B, SENSOR_DATA_MOCK_B)
}

# Plant selection dropdown
selected_plant_name = st.selectbox(
    "Select a Plant", 
    options=list(PLANTS.keys()),
    index=0
)

# Get selected plant and sensor data
selected_plant, selected_sensor_data = PLANTS[selected_plant_name]

# --- Helper functions ---
def moisture_gauge_chart(plant, sensor_data):
    evaluation = evaluate_moisture(plant, sensor_data.moisture)
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=sensor_data.moisture,
        title={"text": f"{plant.name} Moisture"},
        gauge={
            "axis": {"range": [None, 100]},
            "threshold": {
                "line": {"color": "darkgreen", "width": 8},
                "thickness": 0.75,
                "value": plant.moisture_threshold
            },
            "bar": {"color": "black"},
            "steps": [
                {"range": [0, plant.moisture_threshold * 0.6], "color": "red"},
                {"range": [plant.moisture_threshold * 0.6, plant.moisture_threshold * 0.8], "color": "orange"},
                {"range": [plant.moisture_threshold * 0.8, plant.moisture_threshold * 1.2], "color": "green"},
                {"range": [plant.moisture_threshold * 1.2, plant.moisture_threshold * 1.4], "color": "orange"},
                {"range": [plant.moisture_threshold * 1.4, 100], "color": "red"}
            ]
        }
    ))
    fig.update_layout(margin=dict(t=50, b=10))
    return fig

# --- Display Plant Information ---
st.header("Plant Information")
plant_info = pd.DataFrame([{
    "Name": selected_plant.name,
    "Species": selected_plant.species,
    "Moisture Threshold": f"{selected_plant.moisture_threshold}%",
    "Location": selected_plant.location
}])
st.table(plant_info)

# --- Display Sensor Data ---
st.header("Current Sensor Readings")
evaluation = evaluate_moisture(selected_plant, selected_sensor_data.moisture)

# Status card
st.subheader(f"{evaluation['icon']} {selected_plant.name}")
st.markdown(
    f"<div style='border-left: 4px solid {evaluation['color']}; padding: 0.5em; margin-bottom: 1em;'>"
    f"💧 <strong>Status:</strong> {evaluation['status']} - {evaluation['detail']}</div>",
    unsafe_allow_html=True
)

# Gauge chart
st.plotly_chart(moisture_gauge_chart(selected_plant, selected_sensor_data), use_container_width=True)

# Metrics
col1, col2 = st.columns(2)
with col1:
    st.metric("Moisture Level", f"{selected_sensor_data.moisture}%")
with col2:
    st.metric("Temperature", f"{selected_sensor_data.temperature}°C")

st.caption(f"Last updated: {selected_sensor_data.created_at.strftime('%Y-%m-%d %H:%M')}")

# Add status legend
st.markdown("""
<div style="display: flex; justify-content: space-between; margin-top: -10px;">
    <div style="text-align: center;">
        <div style="background-color: red; width: 20px; height: 20px; margin: 0 auto;"></div>
        <small>Danger</small>
    </div>
    <div style="text-align: center;">
        <div style="background-color: orange; width: 20px; height: 20px; margin: 0 auto;"></div>
        <small>Warning</small>
    </div>
    <div style="text-align: center;">
        <div style="background-color: green; width: 20px; height: 20px; margin: 0 auto;"></div>
        <small>Optimal</small>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Line Plot of Historical Data (Daily Minimum) ----
#ISSUE: with matplotlib and streamlit background colors
st.markdown("---")
st.header("Historical Moisture Levels")
st.caption("Daily minimum moisture levels over the past 30 days")

# Get historical data (30 days)
history_df = MockSensorDataDB.get_historical_readings(
    plant_id=selected_plant.id, 
    last_n_days=30
)

# Only proceed if we have data
if not history_df.empty:
    # Convert to datetime and extract date part
    if not pd.api.types.is_datetime64_any_dtype(history_df['created_at']):
        history_df['created_at'] = pd.to_datetime(history_df['created_at'])
    
    # Create date-only column (without time)
    history_df['date'] = history_df['created_at'].dt.date
    
    # Find minimum moisture per day
    daily_min = history_df.groupby('date')['moisture'].min().reset_index()
    daily_min['date'] = pd.to_datetime(daily_min['date'])
    
    # Create line plot
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Set transparent background to match Streamlit
    fig.patch.set_alpha(0.0)
    ax.set_facecolor('none')
    
    # Soft background colors
    soft_red = '#ffcccc'
    soft_orange = '#ffe5cc'
    soft_green = '#e6ffe6'
    
    # Create background zones
    threshold = selected_plant.moisture_threshold
    ax.axhspan(0, threshold * 0.6, color=soft_red, alpha=0.8, label='Danger Zone (Dry)')
    ax.axhspan(threshold * 0.6, threshold * 0.8, color=soft_orange, alpha=0.8, label='Warning Zone (Dry)')
    ax.axhspan(threshold * 0.8, threshold * 1.2, color=soft_green, alpha=0.8, label='Optimal Zone')
    ax.axhspan(threshold * 1.2, threshold * 1.4, color=soft_orange, alpha=0.8, label='Warning Zone (Wet)')
    ax.axhspan(threshold * 1.4, 100, color=soft_red, alpha=0.8, label='Danger Zone (Wet)')
    
    # Plot daily minimum moisture
    ax.plot(daily_min['date'], 
            daily_min['moisture'], 
            marker='o', 
            markersize=8,
            linestyle='-',
            linewidth=2,
            color='#123b5a',
            label='Daily Minimum Moisture')
    
    # Add threshold line
    ax.axhline(y=threshold, color='darkgreen', linestyle='--', linewidth=1.5, alpha=0.7, 
               label=f'Threshold ({threshold}%)')
    
    # Customize plot
    ax.set_title(f"{selected_plant.name} Daily Minimum Moisture", fontsize=16, pad=15, color = 'white')
    ax.set_xlabel("Date", fontsize=12, color='white')
    ax.set_ylabel("Moisture Level (%)", fontsize=12, color='white')
    ax.set_ylim(0, 100)
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    
    # Format x-axis dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    fig.autofmt_xdate(rotation=45)
    
    # Add legend with theme-adaptive styling
    legend = ax.legend(loc='best', framealpha=0.8)
    legend.get_frame().set_facecolor('white')
    legend.set_alpha(0.7)
    
    st.pyplot(fig)
else:
    st.warning("No historical data available for this plant.")

# --- Health Status and Recommendations ---
st.markdown("---")
st.header("Health Status & Recommendations")
status_col, rec_col = st.columns([1, 2])

with status_col:
    # Status indicator with color
    st.markdown(f"### Current Status: <span style='color:{evaluation['color']};'>{evaluation['status']}</span>", 
                unsafe_allow_html=True)
    
    # Health status icon
    if evaluation["status"] == "Optimal":
        st.markdown("<div style='font-size: 80px; text-align: center;'>🌿</div>", unsafe_allow_html=True)
    elif evaluation["status"] == "Warning":
        st.markdown("<div style='font-size: 80px; text-align: center;'>⚡</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div style='font-size: 80px; text-align: center;'>🥀</div>", unsafe_allow_html=True)

with rec_col:
    st.subheader("Recommendations")
    if evaluation["status"] == "Optimal":
        st.success("🌞**Maintain current care routine**")
        st.write("Your plant is thriving! Continue with your current watering schedule and environment.")
        st.progress(0.9, text="Optimal health")
    elif evaluation["status"] == "Warning":
        st.warning("🌥️ **Adjust care routine**")
        if "dry" in evaluation["detail"].lower():
            st.write("💧 **Water within 1-2 days**")
            st.write("Check soil moisture 1 inch below surface. Water thoroughly if dry.")
            st.progress(0.6, text="Moderate attention needed")
        else:
            st.write("🌊 **Improve drainage & reduce watering**")
            st.write("Allow soil to dry between waterings. Ensure proper drainage.")
            st.progress(0.4, text="Moderate attention needed")
    else:
        st.error("⛈️ **Immediate action required**")
        if "dry" in evaluation["detail"].lower():
            st.write("💦 **Water immediately**")
            st.write("Soak thoroughly until water drains from the bottom. Check for root damage.")
            st.progress(0.2, text="Urgent attention needed")
        else:
            st.write("🚑 **Check for root rot**")
            st.write("Stop watering immediately. Remove from pot, trim damaged roots, and repot in dry soil.")
            st.progress(0.1, text="Urgent attention needed")

# Footer
st.markdown("---")
st.markdown("🌱 **Made with care by Sip Sip Cactus** 💚")