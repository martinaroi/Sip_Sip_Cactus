from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional, ClassVar
import logging

from plant_health_tracker.config.base import DEVELOPMENT_MODE
from plant_health_tracker.models.base import Base
from plant_health_tracker.models.sensor_data import SensorDataDB
from plant_health_tracker.models.plant import PlantDB
# Get list of Plants from the database
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from plant_health_tracker.db.database import DatabaseConnection
db = DatabaseConnection()
session = db.get_session()
plants = PlantDB.get_plant_list(session)
logger.info(f"Found {len(plants)} plants:")
for plant in plants:
    logger.info(plant)

# Get Plant with ID 1
plant = PlantDB.get_plant(session, 1)
logger.info(f"Found plant with ID 1: {plant}")
logger.info(f"Found plant with ID 1: {plant.name}")

