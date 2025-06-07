from plant_health_tracker.models import PlantDB, SensorDataDB

plant_list = PlantDB.get_plant_list()
print(plant_list)


PLANTS = {
    plant.name: (plant, SensorDataDB.get_latest_reading(plant.id))
    for plant in plant_list
}

df = SensorDataDB.get_historical_readings(plant_id=1, last_n_days=30)
print(df.head())

# Get historical data (30 days)
#history_df = MockSensorDataDB.get_historical_readings(
#    plant_id=selected_plant.id, 
#    last_n_days=30
#)

