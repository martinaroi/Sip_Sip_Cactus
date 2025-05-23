# Import order is important to avoid circular references
# from .base import Base
# Import models after the base to ensure proper registration
from .plant import PlantDB, Plant
from .sensor_data import SensorDataDB, SensorData