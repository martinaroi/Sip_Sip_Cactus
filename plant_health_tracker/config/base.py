import os
from dotenv import load_dotenv
from pathlib import Path


DEVELOPMENT_MODE = True
ROOT_DIR = Path(__file__).resolve().parent.parent.parent


if os.getenv('ENVIRONMENT') == 'production' or not DEVELOPMENT_MODE:
    env_file = ROOT_DIR / 'env' / 'production.env'
else:
    env_file = ROOT_DIR / 'env' / 'development.env'

load_dotenv(dotenv_path=env_file)

OPENAI_API_TOKEN = os.getenv('OPENAI_API_TOKEN')
MESSANGER_API_TOKEN = os.getenv('MESSANGER_API_TOKEN')

DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')