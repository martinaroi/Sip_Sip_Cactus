from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional, ClassVar
import logging

from plant_health_tracker.config.base import DEVELOPMENT_MODE
from plant_health_tracker.models import SensorDataDB, PlantDB
# Get list of Plants from the database
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

plants = PlantDB.get_plant_list()
logger.info(f"Found {len(plants)} plants:")
logger.info('----- Available Plants -----')
for plant in plants:
    logger.info(repr(plant))
logger.info('-'*20)

# Get Plant with ID 1
plant = PlantDB.get_plant(1)
logger.info(f"Found plant with ID 1: {plant}")
logger.info(f"Found plant with ID 1: {plant.name}")

