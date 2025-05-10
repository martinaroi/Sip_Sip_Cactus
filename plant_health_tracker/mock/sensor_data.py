from datetime import datetime
import pandas as pd
from plant_health_tracker.config.base import TIMEZONE
from ..models.sensor_data import SensorData

# Adding sensor data mocks to match SensorData model
SENSOR_DATA_MOCK_A = SensorData(
    id=1,
    moisture=75.5,
    temperature=22.3,
    plant_id=1,
    created_at=datetime.now(TIMEZONE)
)

SENSOR_DATA_MOCK_B = SensorData(
    id=2,
    moisture=10.2,
    temperature=25.7,
    plant_id=2,
    created_at=datetime.now(TIMEZONE)
)

class MockSensorDataDB():
    """Database model for sensor data.
    This model represents the sensor readings for a plant, including moisture and temperature levels. 
    It is linked to the Plant model through a foreign key relationship.
    """

    @classmethod
    def get_latest_reading(cls, db_session, plant_id: int):
        from ..models.sensor_data import SensorData
        if plant_id == 1:
            # For development purposes, return a mock reading
            return SENSOR_DATA_MOCK_A
            
        elif plant_id == 2:
            # For development purposes, return a mock reading
            return SENSOR_DATA_MOCK_B
        else:
            # For development purposes, return a mock reading
            return SENSOR_DATA_MOCK_A
        

    @classmethod
    def get_historical_readings(cls, db_session, plant_id: int, last_n_days: int = 7) -> pd.DataFrame:
        """Retrieves historical sensor readings for a given plant over the last n days.
        Args:
            db_session: SQLAlchemy session object
            plant_id ID of the plant to retrieve historical readings for
            last_n_days Number of days to look back for historical readings
        Returns:
            DataFrame containing historical sensor readings with date, moisture, and temperature
        """
        from datetime import timedelta
        import random
        import pandas as pd
        
        data = []
        base_time = datetime.now(TIMEZONE)
        
        for i in range(last_n_days):
            # Generate data points for past days
            entry_time = base_time - timedelta(days=i)
            
            # Generate realistic but slightly random values
            if plant_id == 1:  # Venus flytrap - likes moisture
                moisture = 15.0 + random.uniform(-15, 5)
                temperature = 15.0 + random.uniform(-3, 3)
            else:  # Cactus - likes dry conditions
                moisture = 80.0 + random.uniform(-5, 15)
                temperature = 40.0 + random.uniform(-2, 5)
                
            data.append({
                "created_at": entry_time,
                "moisture": round(moisture, 1),
                "temperature": round(temperature, 1),
            })
        
        # Convert to pandas DataFrame
        return pd.DataFrame(data)

# Example usage: print the first 5 rows of the DataFrame
if __name__ == "__main__":
    df = MockSensorDataDB.get_historical_readings(None, 1, last_n_days=5)
    print(df.head())