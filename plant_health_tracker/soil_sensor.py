import time
import board
import busio
from adafruit_seesaw.seesaw import Seesaw

from plant_health_tracker.models.sensor_data import SensorDataDB
from plant_health_tracker.db import DatabaseConnection

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

def read_and_save_sensor_data(plant_id: int):
    try:
        # Read raw moisture value
        raw_moisture = ss.moisture_read()
        temperature = ss.get_temp()
        moisture_percentage = convert_to_percentage(raw_moisture)

        # Print for confirmation
        print(f"Moisture: {moisture_percentage}%, Temperature: {temperature}°C")

        # Save to database
        db = DatabaseConnection()
        session = db.get_session()

        new_reading = SensorDataDB(
            moisture=moisture_percentage,
            temperature=temperature,
            plant_id=plant_id 
        )

        session.add(new_reading)
        session.commit()
        print("Sensor data saved successfully.")

    except Exception as e:
        print(f"Error reading or saving sensor data: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    plant_id = 1
    read_and_save_sensor_data(plant_id)
