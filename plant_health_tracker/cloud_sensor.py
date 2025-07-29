import time
from datetime import datetime
import os
from plant_health_tracker.models.sensor_data import SensorDataDB
from plant_health_tracker.db import DatabaseConnection
from plant_health_tracker.config.base import TIMEZONE

# Check if running in cloud environment
CLOUD_MODE = os.environ.get("CLOUD_MODE", "false").lower() == "true"

if not CLOUD_MODE:
    # Local mode with hardware access
    from adafruit_seesaw.seesaw import Seesaw
    import board
    import busio

    # Create I2C bus and sensor
    i2c_bus = busio.I2C(board.D3, board.D2)
    ss = Seesaw(i2c_bus, addr=0x36)
    
    # Calibration values (adjust to your soil & sensor)
    DRY_VALUE = 200
    WET_VALUE = 600

    def read_sensor():
        """Read actual sensor data"""
        raw_moisture = ss.moisture_read()
        temperature = ss.get_temp()
        moisture_percentage = convert_to_percentage(raw_moisture)
        return moisture_percentage, temperature

else:
    # Cloud mode - mock sensor data
    def read_sensor():
        """Generate mock sensor data for cloud environment"""
        # Simulate values within typical range
        mock_moisture = 40.0 + (time.time() % 20)  # Oscillates between 40-60
        mock_temp = 22.0 + (time.time() % 5)        # Oscillates between 22-27
        return mock_moisture, mock_temp

def convert_to_percentage(raw_value):
    """Convert raw moisture reading to percentage (0-100%)"""
    if not CLOUD_MODE:
        constrained = max(DRY_VALUE, min(WET_VALUE, raw_value))
        percentage = ((constrained - DRY_VALUE) / (WET_VALUE - DRY_VALUE)) * 100
        return round(percentage, 1)
    return raw_value  # In cloud mode, we already have percentages

def read_and_save_sensor_data(session, plant_id: int):
    try:
        moisture, temperature = read_sensor()
        timestamp = datetime.now(TIMEZONE)

        new_reading = SensorDataDB(
            moisture=moisture,
            temperature=temperature,
            created_at=timestamp,
            plant_id=plant_id 
        )

        session.add(new_reading)
        session.commit()
        print(f"Sensor data saved: {moisture}% moisture, {temperature}°C")

    except Exception as e:
        print(f"Error reading or saving sensor data: {e}")
        session.rollback()

if __name__ == "__main__":
    plant_id = 1
    db = DatabaseConnection()
    session = db.get_session()

    try: 
        while True:
            read_and_save_sensor_data(session, plant_id)
            time.sleep(60) # Read every 60 sec
    except KeyboardInterrupt:
        print("Stopped by user")
    finally: 
        session.close()