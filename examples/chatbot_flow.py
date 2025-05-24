from plant_health_tracker.models import PlantDB, SensorDataDB
import asyncio
from plant_health_tracker.telegram_bot import PlantTelegramBot
from plant_health_tracker.config import TELEGRAM_GROUP_CHAT_ID
plant = PlantDB.get_plant(1)  # Replace with the actual plant ID you want to test    
print(plant)
sensor_data = SensorDataDB.get_latest_reading(plant.id)
print(sensor_data)

from plant_health_tracker.plant_ai_bot import PlantChatbot
plant_bot = PlantChatbot()
plant_message = plant_bot.get_daily_notification(plant, sensor_data=sensor_data)
print(plant_message)
# Run async telegram message in console
telegram = PlantTelegramBot()
asyncio.run(telegram.send_message(
    message=plant_message,
    plant_name=plant.name,
    chat_id=TELEGRAM_GROUP_CHAT_ID
))