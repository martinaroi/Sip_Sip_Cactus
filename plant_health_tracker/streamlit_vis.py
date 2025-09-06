import streamlit as st
import os
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Any
try:
    if st.secrets and 'database' in st.secrets:
        os.environ["DB_HOST"] = st.secrets["database"]["DB_HOST"]
        os.environ["DB_PORT"] = str(st.secrets["database"]["DB_PORT"])
        os.environ["DB_NAME"] = st.secrets["database"]["DB_NAME"]
        os.environ["DB_USER"] = st.secrets["database"]["DB_USER"]
        os.environ["DB_PASSWORD"] = st.secrets["database"]["DB_PASSWORD"]
except Exception as e:
    print(f"Error loading database secrets from secrets.toml: {e}")

from plant_health_tracker.mock.plant_data import PLANT_MOCK_A, PLANT_MOCK_B
from plant_health_tracker.mock.sensor_data import SENSOR_DATA_MOCK_A, SENSOR_DATA_MOCK_B, MockSensorDataDB
from plant_health_tracker.utils.moisture_evaluation import evaluate_moisture
from plant_health_tracker.plant_ai_bot import PlantChatbot
from plant_health_tracker.db.database import DatabaseConnection
from plant_health_tracker.models.plant import Plant, PlantDB
from plant_health_tracker.models.sensor_data import SensorDataDB

st.set_page_config(page_title="Plant Health Dashboard", layout="centered")
st.title("🌵 Plant Health Dashboard 🌱")

# # MOCK: Create a dictionary of available plants
# PLANTS = {
#     PLANT_MOCK_A.name: (PLANT_MOCK_A, SENSOR_DATA_MOCK_A),
#     PLANT_MOCK_B.name: (PLANT_MOCK_B, SENSOR_DATA_MOCK_B)
# }

@st.cache_resource
def get_db_connection():
    """Creates a single, cached database connection instance."""
    return DatabaseConnection()

@st.cache_data(ttl=600) # Cache plant list for 10 minutes
def load_all_plants(_db: DatabaseConnection) -> list[Plant]:
    """Fetches all plants from the database and returns Pydantic models.
    Falls back to mock plants if DB is not reachable.
    """
    try:
        with _db.get_session() as session:
            plant_rows = session.query(PlantDB).all()
            return [Plant.model_validate(p) for p in plant_rows]
    except Exception as e:
        # Fallback to mocks so the app still renders
        from plant_health_tracker.mock.plant_data import PLANT_MOCK_A, PLANT_MOCK_B
        st.warning("Database not available; showing mock plants.")
        return [PLANT_MOCK_A, PLANT_MOCK_B]

@st.cache_data(ttl=55) # Cache latest reading for 55 seconds (just under sensor interval)
def get_latest_sensor_reading(_db: DatabaseConnection, plant_id: int) -> SensorDataDB:
    """Fetches the most recent sensor reading for a specific plant. Falls back to mock."""
    try:
        average_over_n_minutes = 15
        sensor_data = SensorDataDB.get_last_n_readings(plant_id=plant_id, n=average_over_n_minutes)
        sensor_data['smoothed_temperature'] = sensor_data['temperature'].ewm(alpha=0.1, adjust=False).mean()
        sensor_data['smoothed_moisture'] = sensor_data['moisture'].ewm(alpha=0.1, adjust=False).mean()
        moisture_last = sensor_data['smoothed_moisture'].iloc[-1].item()
        temperature_last = sensor_data['smoothed_temperature'].iloc[-1].item()
        from plant_health_tracker.models import SensorData
        return SensorData(moisture=moisture_last, temperature=temperature_last, plant_id=plant_id, id=0)
    except Exception:
        st.info("Using mock sensor reading (DB not available).")
        return MockSensorDataDB.get_latest_reading(plant_id)

@st.cache_data(ttl=600) # Cache historical data for 10 minutes
def get_historical_readings(_db: DatabaseConnection, plant_id: int, last_n_days: int = 30) -> pd.DataFrame:
    """Fetches historical sensor readings and returns them as a DataFrame.
    Falls back to mock data if DB is not reachable.
    """
    try:
        with _db.get_session() as session:
            start_date = datetime.utcnow() - timedelta(days=last_n_days)
            query = session.query(
                SensorDataDB.created_at,
                SensorDataDB.moisture
            ).filter(
                SensorDataDB.plant_id == plant_id,
                SensorDataDB.created_at >= start_date
            ).statement

            # Use session.connection() to ensure a valid connection object
            with session.connection() as conn:
                df = pd.read_sql(query, conn)
            return df
    except Exception:
        st.info("Using mock historical data (DB not available).")
        return MockSensorDataDB.get_historical_readings(plant_id=plant_id, last_n_days=last_n_days)

@st.cache_data(ttl=55)  # Cache short-term recent readings (~per-minute updates)
def get_recent_readings(_db: DatabaseConnection, plant_id: int, minutes: int = 10) -> pd.DataFrame | None:
    """Fetch recent sensor readings within the last N minutes.
    Returns a DataFrame with created_at and moisture or None on failure.
    """
    try:
        with _db.get_session() as session:
            start_ts = datetime.utcnow() - timedelta(minutes=minutes)
            query = session.query(
                SensorDataDB.created_at,
                SensorDataDB.moisture
            ).filter(
                SensorDataDB.plant_id == plant_id,
                SensorDataDB.created_at >= start_ts
            ).order_by(SensorDataDB.created_at.asc()).statement
            with session.connection() as conn:
                df = pd.read_sql(query, conn)
            return df
    except Exception:
        # In mock/demo mode we don't have minute-level data
        return None

db = get_db_connection()
all_plants = load_all_plants(db)

if not all_plants:
    st.error("No plants found in the database. Please add plants and ensure the sensor script is running.")
    st.stop()

PLANTS_MAP = {plant.name: plant for plant in all_plants}

selected_plant_name = st.selectbox("Select a Plant", options=list(PLANTS_MAP.keys()))
selected_plant = PLANTS_MAP[selected_plant_name]
selected_sensor_data = get_latest_sensor_reading(db, selected_plant.id)

if not selected_sensor_data:
    st.warning(f"No sensor data found for {selected_plant.name}. Displaying default values.")
    selected_sensor_data = SensorDataDB(moisture=0, temperature=0, created_at=datetime.utcnow())

# # MOCK: Plant selection dropdown
# selected_plant_name = st.selectbox(
#     "Select a Plant", 
#     options=list(PLANTS.keys()),
#     index=0
#)

## MOCK: Get selected plant and sensor data
#selected_plant, selected_sensor_data = PLANTS[selected_plant_name]

# --- Helper functions ---
def moisture_gauge_chart(plant, moisture_value: float):
    evaluation = evaluate_moisture(plant, moisture_value)
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=moisture_value,
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

def _to_float(val: Any, default: float = 0.0) -> float:
    try:
        if val is None:
            return default
        return float(val)
    except Exception:
        return default

def get_api_key():
    """Get API key from multiple sources with priority to Streamlit secrets"""
    api_key = None
    
    # 1. First check Streamlit secrets
    try:
        if hasattr(st.secrets, "openai") and "api_token" in st.secrets.openai:
            api_key = st.secrets.openai.api_token
    except Exception:
        pass
    
    # 2. If not found, try environment variables
    if not api_key:
        api_key = os.getenv("OPENAI_API_TOKEN") or os.getenv("OPENAI_API_KEY")
    
    # 3. If still not found, try .env files
    if not api_key:
        try:
            from dotenv import load_dotenv
            # Try development first, then production
            if not load_dotenv("env/development.env"):
                load_dotenv("env/production.env")
            api_key = os.getenv("OPENAI_API_TOKEN") or os.getenv("OPENAI_API_KEY")
        except ImportError:
            pass
    return api_key

#Initialize chatbot
@st.cache_resource
def get_plant_bot():
    api_key = get_api_key()
    
    if api_key:
        try:
            # Pass the token as api_key to PlantChatbot
            return PlantChatbot(api_key=api_key)
        except Exception as e:
            st.error(f"Failed to initialize chatbot: {str(e)}")
            return None
    else:
        st.warning("OpenAI API key is missing. Chatbot features disabled.")
        return None

plant_bot = get_plant_bot()

# ---Plant Quote of the day ---
# #Display quote
if plant_bot is not None:
    try: 
        daily_quote = plant_bot.get_summary(selected_plant, selected_sensor_data)
    except Exception as e:
        daily_quote = f"Error generating quote: {str(e)}"
else:
    daily_quote = "Chatbot disabled - missing API key"

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

# Gauge chart with optional 10-minute rolling mean 
recent_df = get_recent_readings(db, selected_plant.id, minutes=10)
rolling_value = None

if recent_df is not None and not recent_df.empty:
    dfr = recent_df.copy()
    
    # --- Data Preparation ---
    if not pd.api.types.is_datetime64_any_dtype(dfr['created_at']):
        dfr['created_at'] = pd.to_datetime(dfr['created_at'])
    dfr = dfr.sort_values('created_at', ascending=True)
    dfr['moisture_numeric'] = pd.to_numeric(dfr['moisture'], errors='coerce')

    # --- Rolling Mean Calculation ---
    if len(dfr) >= 3:
        # Calculate the rolling mean with a window of 10 points
        dfr['moisture_rolling'] = dfr['moisture_numeric'].rolling(window=10, min_periods=1).mean()
        rolling_value = dfr['moisture_rolling'].iloc[-1]

# --- Determine the Gauge Value ---
gauge_value = _to_float(selected_sensor_data.moisture) 

if rolling_value is not None and not pd.isna(rolling_value):
    gauge_value = rolling_value

st.plotly_chart(moisture_gauge_chart(selected_plant, gauge_value), use_container_width=True)

# Metrics
col1, col2 = st.columns(2)
with col1:
    st.metric("Moisture Level", f"{int(_to_float(selected_sensor_data.moisture))}%")
with col2:
    st.metric("Temperature", f"{int(_to_float(selected_sensor_data.temperature))}°C")

# Optional: show the rolling mean metric when available
if rolling_value is not None:
    st.caption(f"10-minute rolling mean moisture: {rolling_value:.0f}%")

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
    daily_mean = history_df.groupby('date')['moisture'].mean().reset_index()
    daily_mean['date'] = pd.to_datetime(daily_mean['date'])
    
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
        x=daily_mean['date'],
        y=daily_mean['moisture'],
        mode='lines+markers',
        marker=dict(size=8, color='#123b5a'),
        line=dict(width=2, color='#123b5a'),
        name='Daily Average Moisture'
    ))
    
    # Add threshold line
    fig.add_shape(type="line",
                  x0=daily_mean['date'].mean(), y0=threshold,
                  x1=daily_mean['date'].mean(), y1=threshold,
                  line=dict(color="darkgreen", width=1.5, dash="dash"),
                  name=f'Threshold ({threshold}%)')
    
    # Customize layout
    fig.update_layout(
        title=f"{selected_plant.name} Daily Average Moisture",
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
    if plant_bot is not None:
        try:
            care_tips = plant_bot.get_recommendation(selected_plant, selected_sensor_data)
        except Exception as e:
            care_tips = f"Error generating tips: {str(e)}"
    else:
        care_tips = "Chatbot disabled - missing API key"

    st.markdown(
            f'<div style="background-color:#056915; padding:20px; border-radius:10px; border-left:4px solid #f0fff4">'
    f'<p style="font-size:18px; margin:0;">{care_tips}</p>'
    f'</div>',
    unsafe_allow_html=True
    )

#refresh button
st.caption('Tips refresh every 6 hours. Click below for fresh advice:')
if st.button("🔄 Refresh Care Tips", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Footer
st.markdown("---")
st.markdown("🌱 **Made with care by Sip Sip Cactus** 💚")