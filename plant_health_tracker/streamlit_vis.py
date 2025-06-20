import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from plant_health_tracker.mock.plant_data import PLANT_MOCK_A, PLANT_MOCK_B
from plant_health_tracker.mock.sensor_data import SENSOR_DATA_MOCK_A, SENSOR_DATA_MOCK_B, MockSensorDataDB
from plant_health_tracker.utils.moisture_evaluation import evaluate_moisture
from plant_health_tracker.plant_ai_bot import PlantChatbot

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

#Initialize chatbot
@st.cache_resource
def get_plant_bot():
        return PlantChatbot()

plant_bot = get_plant_bot()

# ---Plant Quote of the day ---
# #Display quote
try: 
    daily_quote = plant_bot.get_summary(selected_plant, selected_sensor_data)
except Exception:
    daily_quote = f"{selected_plant.name} is feeling mysterious today!"

st.markdown(
    f'<div style="background-color:#04549b; padding:15px; border-radius:10px; border-left:4px solid  #f0f8ff; margin-bottom:20px">'
    f'<p style="font-style:italic; font-size:18px; margin:0;">"{daily_quote}"</p>'
    f'<p style="text-align:right; font-size:14px; margin-top:5px;">— {selected_plant.name}\'s Daily Thought</p>'
    f'</div>',
    unsafe_allow_html=True
)

# --- Display Plant Information ---
st.divider()
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
    
    #create figure
    fig = go.Figure()

    #add background zones
    if selected_plant.moisture_threshold:
        threshold = selected_plant.moisture_threshold
        fig.add_shape(type="rect", xref="paper", yref="y",
                    x0=0, y0=0, x1=1, y1=threshold * 0.6,
                    fillcolor="#ffcccc", opacity=0.4, layer="below", line_width=0)
        
        fig.add_shape(type="rect", xref="paper", yref="y",
                    x0=0, y0=threshold * 0.6, x1=1, y1=threshold * 0.8,
                    fillcolor="#ffe5cc", opacity=0.4, layer="below", line_width=0)
        
        fig.add_shape(type="rect", xref="paper", yref="y",
                    x0=0, y0=threshold * 0.8, x1=1, y1=threshold * 1.2,
                    fillcolor="#e6ffe6", opacity=0.4, layer="below", line_width=0)
        fig.add_shape(type="rect", xref="paper", yref="y",
                    x0=0, y0=threshold * 1.2, x1=1, y1=threshold * 1.4,
                    fillcolor="#ffe5cc", opacity=0.4, layer="below", line_width=0)
        
        fig.add_shape(type="rect", xref="paper", yref="y",
                    x0=0, y0=threshold * 1.4, x1=1, y1=100,
                    fillcolor="#ffcccc", opacity=0.4, layer="below", line_width=0)
    else:
        threshold = 50 # Default threshold if not set

    # Add daily minimum line
    fig.add_trace(go.Scatter(
        x=daily_min['date'],
        y=daily_min['moisture'],
        mode='lines+markers',
        marker=dict(size=8, color='#123b5a'),
        line=dict(width=2, color='#123b5a'),
        name='Daily Minimum Moisture'
    ))
    
    # Add threshold line
    fig.add_shape(type="line",
                  x0=daily_min['date'].min(), y0=threshold,
                  x1=daily_min['date'].max(), y1=threshold,
                  line=dict(color="darkgreen", width=1.5, dash="dash"),
                  name=f'Threshold ({threshold}%)')
    
    # Customize layout
    fig.update_layout(
        title=f"{selected_plant.name} Daily Minimum Moisture",
        xaxis_title="Date",
        yaxis_title="Moisture Level (%)",
        yaxis_range=[0, 100],
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#0E1117"),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    # Format x-axis dates
    fig.update_xaxes(
        tickformat="%b %d",
        tickangle=45
    )
    
    # Add zone labels
    fig.add_annotation(text="Danger (Dry)", xref="paper", yref="y",
                       x=0.01, y=threshold * 0.3, showarrow=False,
                       font=dict(color="#0E1117"))
    
    fig.add_annotation(text="Warning (Dry)", xref="paper", yref="y",
                       x=0.01, y=threshold * 0.7, showarrow=False,
                       font=dict(color="#0E1117"))
    
    fig.add_annotation(text="Optimal", xref="paper", yref="y",
                       x=0.01, y=threshold * 1.0, showarrow=False,
                       font=dict(color="#0E1117"))
    
    fig.add_annotation(text="Warning (Wet)", xref="paper", yref="y",
                       x=0.01, y=threshold * 1.3, showarrow=False,
                       font=dict(color="#0E1117"))
    
    fig.add_annotation(text="Danger (Wet)", xref="paper", yref="y",
                       x=0.01, y=threshold * 1.7, showarrow=False,
                       font=dict(color="#0E1117"))
    
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("No historical data available for this plant.")

# --- Health Status and Recommendations ---
st.markdown("---")
st.header("Health Status & Recommendations")
status_col, rec_col = st.columns([1, 2])

# @st.cache_data(ttl=timedelta(hours = 6))
# def get_care_tips(plant, sensor_data):
#     try:
#         return plant_bot.get_recommendation(plant, sensor_data)
#     except Exception:
#         return f"Give {plant.name} some love and attention today!"

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
    st.subheader("🌿 PlantyAI Care Tips")
    #care_tips = get_care_tips(selected_plant, selected_sensor_data)
    try:
        care_tips = plant_bot.get_recommendation(selected_plant, selected_sensor_data)
    except Exception:
        care_tips = f"Give {selected_plant.name} some love and attention today!"
    st.markdown(
            f'<div style="background-color:#056915; padding:20px; border-radius:10px; border-left:4px solid #f0fff4">'
    f'<p style="font-size:18px; margin:0;">{care_tips}</p>'
    f'</div>',
    unsafe_allow_html=True
    )
    # if evaluation["status"] == "Optimal":
    #     st.success("🌞**Maintain current care routine**")
    #     st.write("Your plant is thriving! Continue with your current watering schedule and environment.")
    #     st.progress(0.9, text="Optimal health")
    # elif evaluation["status"] == "Warning":
    #     st.warning("🌥️ **Adjust care routine**")
    #     if "dry" in evaluation["detail"].lower():
    #         st.write("💧 **Water within 1-2 days**")
    #         st.write("Check soil moisture 1 inch below surface. Water thoroughly if dry.")
    #         st.progress(0.6, text="Moderate attention needed")
    #     else:
    #         st.write("🌊 **Improve drainage & reduce watering**")
    #         st.write("Allow soil to dry between waterings. Ensure proper drainage.")
    #         st.progress(0.4, text="Moderate attention needed")
    # else:
    #     st.error("⛈️ **Immediate action required**")
    #     if "dry" in evaluation["detail"].lower():
    #         st.write("💦 **Water immediately**")
    #         st.write("Soak thoroughly until water drains from the bottom. Check for root damage.")
    #         st.progress(0.2, text="Urgent attention needed")
    #     else:
    #         st.write("🚑 **Check for root rot**")
    #         st.write("Stop watering immediately. Remove from pot, trim damaged roots, and repot in dry soil.")
    #         st.progress(0.1, text="Urgent attention needed")

#refresh button
st.caption('Tips refresh every 6 hours. Click below for fresh advice:')
if st.button("🔄 Refresh Care Tips", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Footer
st.markdown("---")
st.markdown("🌱 **Made with care by Sip Sip Cactus** 💚")