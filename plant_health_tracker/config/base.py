import os
import pytz
from dotenv import load_dotenv
from pathlib import Path


DEVELOPMENT_MODE = True
USE_MOCKS = False
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
PACKAGE_DIR = Path(__file__).resolve().parent.parent


if os.getenv('ENVIRONMENT') == 'production' or not DEVELOPMENT_MODE:
    env_file = ROOT_DIR / 'env' / 'production.env'
else:
    env_file = ROOT_DIR / 'env' / 'development.env'

load_dotenv(dotenv_path=env_file)

OPENAI_API_TOKEN = os.getenv('OPENAI_API_TOKEN')
MESSANGER_API_TOKEN = os.getenv('MESSANGER_API_TOKEN')

# Telegram API configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_GROUP_CHAT_ID = os.getenv('TELEGRAM_GROUP_CHAT_ID')

DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PORT = os.getenv('DB_PORT')
DB_PASSWORD = os.getenv('DB_PASSWORD')

TIMEZONE = pytz.timezone('Europe/Prague')
