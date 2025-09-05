import logging
import asyncio
import time
from datetime import datetime
from collections import defaultdict
from typing import Optional, List, Dict, Any, Union
import pandas as pd
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError
from telegram.constants import ParseMode
from plant_health_tracker.config.base import TELEGRAM_BOT_TOKEN, TELEGRAM_GROUP_CHAT_ID
from plant_health_tracker.plant_ai_bot import PlantChatbot
from plant_health_tracker.models.plant import Plant


class PlantTelegramBot:
    """
    A class for handling plant-based chatbot interactions via Telegram API.

    This class connects the PlantChatbot functionality to a Telegram bot,
    allowing plants to send messages to a Telegram group chat and receive
    messages from users.

    Attributes:
        API_TIMEOUT (int): Timeout for Telegram API requests in seconds
        RETRY_DELAY (int): Delay between retries for failed API calls in seconds
        MAX_RETRIES (int): Maximum number of retries for failed API calls
        CONVERSATION_MAX_LENGTH (int): Maximum number of messages to keep in conversation history
        CONVERSATION_EXPIRY_TIME (int): Time in seconds after which conversation history expires
        MESSAGE_COOLDOWN (int): Minimum time in seconds between notifications for the same plant
        bot_token (str): Telegram bot API token
        chat_id (str): Default Telegram chat ID for sending messages
        bot (Bot): Telegram Bot instance
        application (Application): Telegram Application instance for long-polling
        logger (Logger): Logger instance for debugging and tracking
        conversation_history (Dict): Dictionary storing conversation history for each plant
        last_message_time (Dict): Dictionary tracking the last message time for each plant
    """
    DEFAULT_PARSE_MODE = ParseMode.MARKDOWN_V2
    API_TIMEOUT = 30
    RETRY_DELAY = 2
    MAX_RETRIES = 3
    CONVERSATION_MAX_LENGTH = 10  # Keep last 10 messages
    CONVERSATION_EXPIRY_TIME = 3600  # Conversation expires after 1 hour
    MESSAGE_COOLDOWN = 300  # 5 minutes between messages for same plant
    TELEGRAM_API_TOKEN = TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID = TELEGRAM_GROUP_CHAT_ID

    def __init__(
        self, 
        plant_chatbot: Optional[PlantChatbot] = PlantChatbot(),
        log_level: int = logging.INFO
    ):
        """
        Initialize the PlantTelegramBot.

        Args:
            bot_token (Optional[str]): Telegram bot token. Defaults to TELEGRAM_BOT_TOKEN.
            chat_id (Optional[str]): Default chat ID to send messages to. Defaults to TELEGRAM_GROUP_CHAT_ID.
            plant_chatbot (Optional[PlantChatbot]): Instance of PlantChatbot. If not provided, one will be created as needed.
            log_level (int): Logging level. Defaults to logging.INFO.

        Raises:
            ValueError: If no valid bot token is provided.
        """
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("Telegram bot token is required. Provide it as an argument or set the TELEGRAM_BOT_TOKEN environment variable.")

        self.plant_chatbot = plant_chatbot
        
        # Setup logging
        self.logger = logging.getLogger("PlantTelegramBot")
        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
        # Initialize bot
        self.bot = Bot(token=self.TELEGRAM_API_TOKEN)
        
        # Initialize application for handling incoming messages
        self.application = Application.builder().token(self.TELEGRAM_API_TOKEN).build()
        
        # Initialize conversation history storage
        # Structure: {plant_id: {"messages": [], "last_active": timestamp}}
        self.conversation_history = defaultdict(lambda: {"messages": [], "last_active": 0})
        
        # Initialize message cooldown tracking
        self.last_message_time = defaultdict(int)
        
    async def setup(self):
        """Set up command handlers for the bot."""
        # Define command handlers
        self.application.add_handler(CommandHandler("start", self._cmd_start))
        self.application.add_handler(CommandHandler("help", self._cmd_help))
        self.application.add_handler(CommandHandler("status", self._cmd_status))
        self.application.add_handler(CommandHandler("plants", self._cmd_list_plants))
        
        # Define message handler for regular messages
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        
        # Error handler
        self.application.add_error_handler(self._error_handler)
        
        self.logger.info("Telegram bot handlers have been set up")
        
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for the /start command."""
        await update.message.reply_text("Hi! I'm just a messanger. I will relay messages to plants while you out!")

    async def _cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for the /help command."""
        help_text = (
            "I can help you communicate with your plants!\n\n"
            "Available commands:\n"
            "/start - Start the bot\n"
            "/help - Show this help message\n"
            "/status - Check the status of all plants\n"
            "/plants - List available plants\n\n"
            "To chat with a specific plant, start your message with their name:\n"
            "Example: 'Vendula, how are you feeling today?'"
        )
        await update.message.reply_text(help_text)
    
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for the /status command to check all plants."""
        # TODO: Reimplement this to check the status of all plants
        await update.message.reply_text("Checking the status of all plants. Please wait...")
        
        if not hasattr(context.bot_data, 'plants') or not context.bot_data.get('plants'):
            await update.message.reply_text("No plants are registered with the bot yet.")
            return
            
        for plant in context.bot_data.get('plants', []):
            # Get sensor data for the plant (not implemented here - would come from your database)
            sensor_data = self._get_plant_sensor_data(plant.id)
            
            if sensor_data is not None:
                await self.send_plant_notification(
                    plant_chatbot=self._get_plant_chatbot(),
                    plant=plant,
                    sensor_data=sensor_data,
                    chat_id=update.effective_chat.id
                )
            else:
                await update.message.reply_text(f"No sensor data available for {plant.name}")
                
    async def _cmd_list_plants(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for the /plants command to list available plants."""
        if not hasattr(context.bot_data, 'plants') or not context.bot_data.get('plants'):
            await update.message.reply_text("No plants are registered with the bot yet.")
            return
            
        plants_text = "Available plants:\n"
        for plant in context.bot_data.get('plants', []):
            plants_text += f"- {plant.name} ({plant.species}) - {plant.persona}\n"
            
        await update.message.reply_text(plants_text)
        
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handler for regular text messages."""
        user_message = update.message.text
        user_name = update.message.from_user.first_name
        chat_id = update.effective_chat.id
        
        # Check if this is directed to a specific plant
        target_plant = None
        
        # If we have plants available in context
        plants = context.bot_data.get('plants', [])
        
        if not plants:
            # This is a demo response - in production, you would fetch plants from database
            from plant_health_tracker.mock.plant_data import PLANT_MOCK_A, PLANT_MOCK_B
            plants = [PLANT_MOCK_A, PLANT_MOCK_B]
        
        # Check if message starts with a plant name
        for plant in plants:
            if user_message.lower().startswith(plant.name.lower()):
                target_plant = plant
                # Remove the plant name from the message
                user_message = user_message[len(plant.name):].lstrip(',:; ')
                break
        
        # If no specific plant was addressed, choose a random one or the first one
        if not target_plant and plants:
            target_plant = plants[0]
        
        if target_plant:
            self.logger.info(f"Message from {user_name} to {target_plant.name}: {user_message}")
            
            # Get conversation history for this plant
            plant_history = self._get_conversation_history(target_plant.id)
            
            # Add user message to history
            self._add_to_conversation_history(
                plant_id=target_plant.id,
                message=f"User: {user_message}"
            )
            
            # Get sensor data for the plant
            sensor_data = self._get_plant_sensor_data(target_plant.id)
            
            # Generate response from the plant
            try:
                chatbot = self._get_plant_chatbot()
                response = chatbot.get_chat_response(
                    user_input=user_message,
                    plant=target_plant,
                    conversation_history=plant_history,
                    user=user_name,
                    sensor_data=sensor_data
                )
                
                # Add plant's response to history
                self._add_to_conversation_history(
                    plant_id=target_plant.id,
                    message=f"Plant: {response}"
                )
                
                # Send the response to the user
                await self.send_plant_message(
                    message=response,
                    chat_id=chat_id,
                    plant_name=target_plant.name
                )
                
            except Exception as e:
                self.logger.error(f"Error generating plant response: {e}")
                await update.message.reply_text(f"Sorry, {target_plant.name} is having trouble communicating right now.")
        else:
            # No plants available
            await update.message.reply_text("Sorry, I don't have any plants registered to chat with you.")
            
    def _get_plant_chatbot(self) -> PlantChatbot:
        """Get or create a PlantChatbot instance."""
        if not self.plant_chatbot:
            self.plant_chatbot = PlantChatbot()
        return self.plant_chatbot
    
    def _add_to_conversation_history(self, plant_id: int, message: str) -> None:
        """
        Add a message to the conversation history for a specific plant.
        
        Args:
            plant_id (int): ID of the plant
            message (str): Message to add to the history
        """
        # Update the last active timestamp
        now = time.time()
        self.conversation_history[plant_id]["last_active"] = now
        
        # Add the message to the history
        self.conversation_history[plant_id]["messages"].append(message)
        
        # Truncate history if it exceeds max length
        if len(self.conversation_history[plant_id]["messages"]) > self.CONVERSATION_MAX_LENGTH:
            self.conversation_history[plant_id]["messages"].pop(0)
    
    def _get_conversation_history(self, plant_id: int) -> List[str]:
        """
        Get the conversation history for a specific plant.
        
        Args:
            plant_id (int): ID of the plant
            
        Returns:
            List[str]: List of conversation messages
        """
        # Check if conversation history exists and hasn't expired
        now = time.time()
        conversation_data = self.conversation_history.get(plant_id, {"messages": [], "last_active": 0})
        
        # If conversation has expired, clear it
        if now - conversation_data["last_active"] > self.CONVERSATION_EXPIRY_TIME:
            self.conversation_history[plant_id]["messages"] = []
            self.conversation_history[plant_id]["last_active"] = now
            
        return self.conversation_history[plant_id]["messages"]
            
    def _get_plant_sensor_data(self, plant_id: int) -> pd.DataFrame:
        """
        Get sensor data for a specific plant.
        
        This is a placeholder method - in a real implementation, you would
        fetch this data from your database or sensor system.
        
        Args:
            plant_id: The ID of the plant to get sensor data for
            
        Returns:
            DataFrame containing sensor data, or None if not available
        """
        try:
            # In a real implementation, fetch from database instead
            from plant_health_tracker.mock.sensor_data import get_sensor_data_as_dataframe
            df = get_sensor_data_as_dataframe()
            
            # Filter for just this plant's data and get the most recent readings
            plant_data = df[df['plant_id'] == plant_id].tail(10)
            
            if plant_data.empty:
                return None
                
            return plant_data
        except Exception as e:
            self.logger.error(f"Error fetching sensor data for plant {plant_id}: {e}")
            return None
            
    async def _error_handler(self, update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors in the Telegram bot."""
        self.logger.error(f"Exception while handling an update: {context.error}")

    async def send_plant_message(
        self, 
        message: str, 
        chat_id: Optional[str] = None, 
        plant_name: Optional[str] = None
    ) -> bool:
        """
        Send a message from a plant to a Telegram chat.

        Args:
            message (str): The message to send
            chat_id (Optional[str]): Chat ID to send to. Defaults to self.chat_id.
            plant_name (Optional[str]): Name of the plant to include with the message.

        Returns:
            bool: True if message was sent successfully, False otherwise
        """
        if not chat_id:
            chat_id = self.TELEGRAM_CHAT_ID
            
        if not chat_id:
            self.logger.error("No chat ID specified for sending message")
            return False
            
        formatted_message = message
        if plant_name:
            formatted_message = f"🌱 {plant_name}: {message}"
            
        for attempt in range(self.MAX_RETRIES):
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=formatted_message,
                    timeout=self.API_TIMEOUT,
                    parse_mode=self.DEFAULT_PARSE_MODE
                )
                self.logger.info(f"Message sent successfully to chat {chat_id}")
                return True
            except TelegramError as e:
                self.logger.error(f"Failed to send message (attempt {attempt+1}/{self.MAX_RETRIES}): {e}")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY)
                else:
                    return False
    
    async def send_plant_notification(
        self, 
        plant_chatbot: PlantChatbot,
        plant: Plant,
        sensor_data: pd.DataFrame,
        chat_id: Optional[str] = None
    ) -> bool:
        """
        Generate and send a plant notification using PlantChatbot.

        Args:
            plant_chatbot (PlantChatbot): Instance of PlantChatbot to generate the message
            plant (Plant): Plant object containing name, species, and personality
            sensor_data (pd.DataFrame): Sensor data for the plant
            chat_id (Optional[str]): Chat ID to send to. Defaults to self.chat_id.

        Returns:
            bool: True if notification was sent successfully, False otherwise
        """
        try:
            notification = plant_chatbot.get_daily_notification(plant, sensor_data)
            return await self.send_plant_message(notification, chat_id, plant.name)
        except Exception as e:
            self.logger.error(f"Error generating or sending plant notification: {e}")
            return False
            
    async def send_scheduled_notifications(self, plants: List[Plant], chat_id: Optional[str] = None) -> Dict[int, bool]:
        """
        Send scheduled notifications for all provided plants.
        
        Args:
            plants (List[Plant]): List of plants to send notifications for
            chat_id (Optional[str]): Chat ID to send to. Defaults to self.chat_id.
            
        Returns:
            Dict[int, bool]: Dictionary mapping plant IDs to success/failure status
        """
        results = {}
        
        for plant in plants:
            # Check if we should send a notification for this plant (based on cooldown)
            if not self._should_allow_message(plant.id):
                self.logger.info(f"Skipping notification for {plant.name} due to rate limiting")
                results[plant.id] = False
                continue
                
            # Get sensor data
            sensor_data = self._get_plant_sensor_data(plant.id)
            
            if sensor_data is None or sensor_data.empty:
                self.logger.warning(f"No sensor data available for {plant.name}")
                results[plant.id] = False
                continue
                
            # Send notification
            success = await self.send_plant_notification(
                plant_chatbot=self._get_plant_chatbot(),
                plant=plant,
                sensor_data=sensor_data,
                chat_id=chat_id
            )
            
            # Update last message time
            if success:
                self._update_last_message_time(plant.id)
                
            results[plant.id] = success
            
        return results
    
    def _should_allow_message(self, plant_id: int) -> bool:
        """
        Check if a plant should be allowed to send a message based on cooldown period.
        
        Args:
            plant_id (int): ID of the plant
            
        Returns:
            bool: True if message is allowed, False if plant is in cooldown period
        """
        now = time.time()
        last_time = self.last_message_time.get(plant_id, 0)
        
        # If enough time has passed since the last message
        return now - last_time >= self.MESSAGE_COOLDOWN
    
    def _update_last_message_time(self, plant_id: int) -> None:
        """
        Update the last message time for a plant.
        
        Args:
            plant_id (int): ID of the plant
        """
        self.last_message_time[plant_id] = time.time()
    
    def register_plants(self, plants: List[Plant]) -> None:
        """
        Register plants with the bot.
        
        Args:
            plants (List[Plant]): List of plants to register
        """
        # This method provides a way to register plants with the bot
        # In a full implementation, we would store this in the bot_data context
        # For this simple version, we'll just log the registration
        self.logger.info(f"Registered {len(plants)} plants with the bot")
        
    async def setup_scheduled_notifications(self, plants: List[Plant], interval: int = 3600) -> asyncio.Task:
        """
        Set up scheduled notifications for plants.
        
        Args:
            plants (List[Plant]): List of plants to send notifications for
            interval (int): Interval in seconds between notifications
            
        Returns:
            asyncio.Task: Task object for the scheduled notifications
        """
        async def scheduled_job():
            self.logger.info(f"Starting scheduled notifications every {interval} seconds")
            while True:
                try:
                    await self.send_scheduled_notifications(plants)
                    self.logger.info(f"Scheduled notifications sent, next run in {interval} seconds")
                except Exception as e:
                    self.logger.error(f"Error sending scheduled notifications: {e}")
                
                await asyncio.sleep(interval)
                
        task = asyncio.create_task(scheduled_job())
        return task
            
    async def run_polling(self):
        """
        Start the bot in polling mode.
        
        This method starts the bot to continuously check for new messages.
        It should be run in an asyncio event loop.
        """
        self.logger.info("Starting bot in polling mode")
        await self.setup()
        await self.application.run_polling(allowed_updates=Update.ALL_TYPES)

    async def start_polling(self) -> None:
        """
        Start the bot polling for messages.
        """
        self.logger.info("Starting bot polling...")
        await self.application.initialize()
        await self.application.start_polling()
        self.logger.info("Bot polling started")

    async def stop_polling(self) -> None:
        """
        Stop the bot polling.
        """
        self.logger.info("Stopping bot...")
        await self.application.stop()
        await self.application.shutdown()
        self.logger.info("Bot stopped")
# Example usage
if __name__ == "__main__":
    from plant_health_tracker.mock.sensor_data import get_sensor_data_as_dataframe
    from plant_health_tracker.mock.plant_data import PLANT_MOCK_A
    
    async def main():
        # Initialize bot
        telegram_bot = PlantTelegramBot()
        
        # Initialize plant chatbot
        plant_bot = PlantChatbot()
        
        # Get sample data
        df = get_sensor_data_as_dataframe()
        recent_data = df.tail(10)
        
        # Example: Send a notification
        success = await telegram_bot.send_plant_notification(
            plant_chatbot=plant_bot,
            plant=PLANT_MOCK_A,
            sensor_data=recent_data
        )
        
        if success:
            print("Notification sent successfully!")
        else:
            print("Failed to send notification")
            
        # Run bot polling in background
        # await telegram_bot.run_polling()
    
    # Run the example
    asyncio.run(main())
