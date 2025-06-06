# Use slim Python image
FROM python:3.12-slim

# Install system dependencies for PostgreSQL drivers and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev python3-dev build-essential curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
ENV POETRY_VERSION=1.8.1 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1
ENV PATH="$POETRY_HOME/bin:$PATH"

RUN curl -sSL https://install.python-poetry.org | python3 -

# Set working directory
WORKDIR /app

# Copy project metadata for dependency installation
COPY pyproject.toml poetry.lock ./

# Install Python dependencies without development packages
RUN poetry install --no-root --no-dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Command to run the Telegram bot
CMD ["python", "-m", "plant_health_tracker.telegram_bot"]
