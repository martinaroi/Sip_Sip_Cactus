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
from plant_health_tracker.utils.telegram import escape_markdown_v2


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
    MAX_RETRIES = 1
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
        self.last_message_time = defaultdict(int)
        
    async def send_plant_message(
        self, 
        message: str, 
        plant_name: Optional[str] = None,
        chat_id: Optional[str] = None, 
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
        
        # Escape the message and plant name for MarkdownV2
        safe_message = escape_markdown_v2(message)
        if plant_name:
            safe_plant_name = escape_markdown_v2(plant_name)
            formatted_message = f"🌱 *{safe_plant_name}*: \n{safe_message}"
            
        for attempt in range(self.MAX_RETRIES):
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=formatted_message,
                    write_timeout=self.API_TIMEOUT,
                    parse_mode='MarkdownV2'
                )
                self.logger.info(f"Message sent successfully to chat {chat_id}")
                return True
            except TelegramError as e:
                self.logger.error(f"Failed to send message (attempt {attempt+1}/{self.MAX_RETRIES}) to chat {chat_id}: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY)
                else:
                    return False
        
if __name__ == "__main__":
    # Example usage
    async def main():
        plant_bot = PlantTelegramBot()
        plant_bot.logger.info("Plant Telegram Bot initialized")
        
        # Send a simple test message
        # await plant_bot.send_plant_message(message="Hello, I am your plant monitor!")
        
        # Send a message from a specific plant
        await plant_bot.send_plant_message(
            message="I'm feeling a bit dry today. Could I get some water?",
            plant_name="Bob the Cactus",
        )
    asyncio.run(main())