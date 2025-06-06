# PlantHealthMonitor

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/release/python-3120/)
![Stars](https://img.shields.io/github/stars/martinaroi/Sip_Sip_Cactus?style=social)
![Contributors](https://img.shields.io/github/contributors/martinaroi/Sip_Sip_Cactus)
![Commits](https://img.shields.io/github/commit-activity/m/martinaroi/Sip_Sip_Cactus)
![Last Commit](https://img.shields.io/github/last-commit/martinaroi/Sip_Sip_Cactus)
![Code Size](https://img.shields.io/github/languages/code-size/martinaroi/Sip_Sip_Cactus)

A comprehensive Python project for monitoring plant health using IoT sensors on Raspberry Pi Zero 2, enabling conversational plant communication via Telegram.

## Table of Contents

- [PlantHealthMonitor](#planthealthmonitor)
  - [Table of Contents](#table-of-contents)
  - [Architecture](#architecture)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
    - [Telegram Bot Setup](#telegram-bot-setup)
  - [Usage](#usage)
    - [Telegram Bot](#telegram-bot)
    - [Streamlit Dashboard](#streamlit-dashboard)


## Architecture

- Python 3.12
- [Poetry](https://python-poetry.org/) for dependency management
- [FastAPI](https://fastapi.tiangolo.com/) for REST services
- [Streamlit](https://streamlit.io/) + [Plotly](https://plotly.com/) for dashboards
- [LangChain](https://langchain.com/) & OpenAI for conversational AI
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot) for notifications
- PostgreSQL to store sensor data
- Raspberry Pi Zero 2 for IoT sensor integration

![Architecture Diagram](./docs/architecture_diagram.png)

## Prerequisites

- Python 3.12+
- Docker & Docker Compose (optional, for containerized deployment)
- PostgreSQL database
- Telegram bot token and target chat/group ID
- OpenAI API key (if using AI features)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/martinaroi/Sip_Sip_Cactus.git
   cd SIP_SIP_CACTUS
   ```
2. Install [Poetry](https://python-poetry.org/docs/#installation) if you haven't already:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```
   Ensure Poetry is in your PATH, or follow the instructions provided by the installer.
3. Install Postgres Headers (if not already installed):
   ```bash
   sudo apt-get install libpq-dev python3-dev
   ```
4. Install dependencies via Poetry:
   ```bash
   poetry install
   ```
5. Copy and customize environment files:
   ```bash
   cp env/env.example env/development.env
   # or use env/production.env for production
   ```

## Configuration

Environment variables are managed via `.env` files in the `env/` directory. At minimum, set the following:

### Telegram Bot Setup
Create a Telegram bot and get your token:
1. Open Telegram and search for `@BotFather`.
2. Start a chat and use the command `/newbot` to create a new bot.
3. Follow the instructions to get your bot token.
4. Get your chat ID by sending a message to your bot and using the `getUpdates` method or a bot like `@userinfobot`.
5. Set the environment variables in your `.env` file:

```bash

```ini
# env/development.env
DATABASE_URL=postgresql://user:password@localhost:5432/plantdb
TELEGRAM_BOT_TOKEN=<your-telegram-bot-token>
TELEGRAM_GROUP_CHAT_ID=<your-chat-id>
OPENAI_API_KEY=<your-openai-api-key>
```

## Usage

### Telegram Bot

Run the Telegram bot:
```bash
poetry run python plant_health_tracker/telegram_bot.py
```
Or use the example:
```bash
poetry run python examples/telegram_bot_example.py
```

### Streamlit Dashboard

Start the dashboard:
```bash
poetry run streamlit run dashboard/app.py
```
Open `http://localhost:8501` in your browser.
