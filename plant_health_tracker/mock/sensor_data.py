import random
from datetime import datetime, timedelta
import pandas as pd

# Generate mock sensor data for every 15 minutes
mock_sensor_data = []
start_time = datetime.now() - timedelta(days=1)  # Start from 24 hours ago

for i in range(50):  # 96 intervals of 15 minutes in 24 hours
    created_at = start_time + timedelta(minutes=15 * i)
    moisture = round(random.uniform(5, 10), 2) 
    temperature = round(random.uniform(15, 35), 2)
    plant_id = random.randint(1, 2) 

    mock_sensor_data.append({
        "created_at": created_at,
        "moisture": moisture,
        "temperature": temperature,
        "plant_id": plant_id
    })

# Convert mock sensor data to a pandas DataFrame
def get_sensor_data_as_dataframe():
    return pd.DataFrame(mock_sensor_data)

# Example usage: print the first 5 rows of the DataFrame
if __name__ == "__main__":
    df = get_sensor_data_as_dataframe()
    print(df.head())