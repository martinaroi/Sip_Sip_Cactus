import asyncio
import pandas as pd
import logging
from plant_health_tracker.telegram_vibe import PlantTelegramBot
from plant_health_tracker.plant_ai_bot import PlantChatbot
from plant_health_tracker.mock.plant_data import PLANT_MOCK_A, PLANT_MOCK_B
from plant_health_tracker.mock.sensor_data import get_sensor_data_as_dataframe

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def send_notifications():
    """Send daily notifications for each plant."""
    # Initialize the bots
    telegram_bot = PlantTelegramBot()
    plant_bot = PlantChatbot()
    
    # Get mock sensor data
    df = get_sensor_data_as_dataframe()
    
    # Filter data for each plant
    plant_a_data = df[df['plant_id'] == PLANT_MOCK_A.id].tail(10)
    plant_b_data = df[df['plant_id'] == PLANT_MOCK_B.id].tail(10)
    
    # Send notifications for each plant
    logger.info(f"Sending notification for {PLANT_MOCK_A.name}")
    success_a = await telegram_bot.send_plant_notification(
        plant_chatbot=plant_bot,
        plant=PLANT_MOCK_A,
        sensor_data=plant_a_data
    )
    
    logger.info(f"Sending notification for {PLANT_MOCK_B.name}")
    success_b = await telegram_bot.send_plant_notification(
        plant_chatbot=plant_bot,
        plant=PLANT_MOCK_B,
        sensor_data=plant_b_data
    )
    
    # Report results
    if success_a and success_b:
        logger.info("All notifications sent successfully!")
    else:
        logger.warning("Some notifications failed to send")

async def run_telegram_bot():
    """Run the Telegram bot in polling mode."""
    telegram_bot = PlantTelegramBot()
    await telegram_bot.run_polling()
    
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--bot":
        # Run the bot in polling mode
        asyncio.run(run_telegram_bot())
    else:
        # Just send notifications
        asyncio.run(send_notifications())
