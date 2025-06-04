import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plant_health_tracker.mock.plant_data import PLANT_MOCK_A, PLANT_MOCK_B
from plant_health_tracker.mock.sensor_data import SENSOR_DATA_MOCK_A, SENSOR_DATA_MOCK_B
from plant_health_tracker.utils.moisture_evaluation import evaluate_moisture

st.set_page_config(page_title="Plant Health Dashboard", layout="centered")
st.title("🌵 Plant Health Dashboard 🌱")

# --- Helper function to display a gauge chart ---
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
            "bar": {"color": evaluation["color"]},
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

# --- Display Plant Info Table ---
st.header("Plant Information")
plant_info = pd.DataFrame([
    {
        "Name": PLANT_MOCK_A.name,
        "Species": PLANT_MOCK_A.species,
        "Moisture Threshold": f"{PLANT_MOCK_A.moisture_threshold}%",
        "Location": PLANT_MOCK_A.location
    },
    {
        "Name": PLANT_MOCK_B.name,
        "Species": PLANT_MOCK_B.species,
        "Moisture Threshold": f"{PLANT_MOCK_B.moisture_threshold}%",
        "Location": PLANT_MOCK_B.location
    }
])
st.table(plant_info)

# --- Display Sensor Data ---
st.header("Current Sensor Readings")
col1, col2 = st.columns(2)

def display_status_card(plant, sensor_data, column):
    evaluation = evaluate_moisture(plant, sensor_data.moisture)
    
    with column:
        st.subheader(f"{evaluation['icon']} {plant.name}")
        
        # Status card with color border
        st.markdown(
            f"<div style='border-left: 4px solid {evaluation['color']}; padding: 0.5em; margin-bottom: 1em;'>"
            f"💧 <strong>Status:</strong> {evaluation['status']} - {evaluation['detail']}</div>",
            unsafe_allow_html=True
        )
        
        # Gauge chart
        st.plotly_chart(moisture_gauge_chart(plant, sensor_data), use_container_width=True)
        
        # Additional metrics
        col_metrics1, col_metrics2 = st.columns(2)
        with col_metrics1:
            st.metric("Moisture Level", f"{sensor_data.moisture}%")
        with col_metrics2:
            st.metric("Temperature", f"{sensor_data.temperature}°C")
            
        st.caption(f"Last updated: {sensor_data.created_at.strftime('%Y-%m-%d %H:%M')}")

display_status_card(PLANT_MOCK_A, SENSOR_DATA_MOCK_A, col1)
display_status_card(PLANT_MOCK_B, SENSOR_DATA_MOCK_B, col2)

# --- Comparison Charts ---
st.header("Plant Comparison")

st.subheader("Moisture Levels")
moisture_df = pd.DataFrame({
    "Plant": [PLANT_MOCK_A.name, PLANT_MOCK_B.name],
    "Moisture": [SENSOR_DATA_MOCK_A.moisture, SENSOR_DATA_MOCK_B.moisture],
    "Threshold": [PLANT_MOCK_A.moisture_threshold, PLANT_MOCK_B.moisture_threshold]
})
st.bar_chart(moisture_df.set_index("Plant"))

st.subheader("Temperature Comparison")
temp_df = pd.DataFrame({
    "Plant": [PLANT_MOCK_A.name, PLANT_MOCK_B.name],
    "Temperature": [SENSOR_DATA_MOCK_A.temperature, SENSOR_DATA_MOCK_B.temperature]
})
st.bar_chart(temp_df.set_index("Plant"))

# --- Health Summary ---
st.header("Health Status Summary")
eval_a = evaluate_moisture(PLANT_MOCK_A, SENSOR_DATA_MOCK_A.moisture)
eval_b = evaluate_moisture(PLANT_MOCK_B, SENSOR_DATA_MOCK_B.moisture)

if eval_a["status"] == "Optimal" and eval_b["status"] == "Optimal":
    st.success("🌼 All plants are in optimal condition!🌻")
elif eval_a["status"] == "Danger" or eval_b["status"] == "Danger":
    st.error("🥀 Some plants need immediate attention!🥀")
    if eval_a["status"] == "Danger":
        st.error(f"{PLANT_MOCK_A.name}: {eval_a['detail']}")
    if eval_b["status"] == "Danger":
        st.error(f"{PLANT_MOCK_B.name}: {eval_b['detail']}")
else:
    st.warning("⚡ Some plants may need attention.⚡")
    if eval_a["status"] == "Warning":
        st.warning(f"{PLANT_MOCK_A.name}: {eval_a['detail']}")
    if eval_b["status"] == "Warning":
        st.warning(f"{PLANT_MOCK_B.name}: {eval_b['detail']}")

# Footer
st.markdown("---")
st.markdown("Made with 💚 by [Sip Sip Cactus]")