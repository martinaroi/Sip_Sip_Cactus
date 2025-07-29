import time
from datetime import datetime
from adafruit_seesaw.seesaw import Seesaw
import board
import busio

from plant_health_tracker.models.sensor_data import SensorDataDB
from plant_health_tracker.db import DatabaseConnection
from plant_health_tracker.config.base import TIMEZONE

# Create I2C bus and sensor
i2c_bus = busio.I2C(board.D3, board.D2)
ss = Seesaw(i2c_bus, addr=0x36)
 
# Calibration values (adjust to your soil & sensor)
DRY_VALUE = 200
WET_VALUE = 600

def convert_to_percentage(raw_value):
    """Convert raw moisture reading to percentage (0-100%)"""
    constrained = max(DRY_VALUE, min(WET_VALUE, raw_value))
    percentage = ((constrained - DRY_VALUE) / (WET_VALUE - DRY_VALUE)) * 100
    return round(percentage, 1)

def read_and_save_sensor_data(session, plant_id: int):
    try:
        # Read raw moisture value
        raw_moisture = ss.moisture_read()
        temperature = ss.get_temp()
        moisture_percentage = convert_to_percentage(raw_moisture)
        timestamp = datetime.now(TIMEZONE)

        new_reading = SensorDataDB(
            moisture=moisture_percentage,
            temperature=temperature,
            created_at = timestamp,
            plant_id=plant_id 
        )

        session.add(new_reading)
        session.commit()
        print("Sensor data saved successfully.")

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
    finally: 
        session.close()
