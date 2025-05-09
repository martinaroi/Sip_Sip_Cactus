import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

from plant_health_tracker.config.base import TELEGRAM_BOT_TOKEN

BOT_TOKEN = TELEGRAM_BOT_TOKEN # Replace with your bot token
print('Bot Token: ',BOT_TOKEN)

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    logger.info(f"Received message in chat with ID: {chat_id}")
    # You can also have the bot reply with the ID
    # await update.message.reply_text(f"This chat's ID is: {chat_id}")

def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    # Add a handler that listens to any text message
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_chat_id))
    logger.info("Bot started. Send a message to the group it's in to get the chat ID.")
    application.run_polling()

if __name__ == "__main__":
    main()
    