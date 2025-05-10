from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import desc
from datetime import datetime, timedelta, timezone
import pandas as pd
import pytz
from pydantic import BaseModel, Field
from typing import Optional

from plant_health_tracker.config.base import TIMEZONE, DEVELOPMENT_MODE

Base = declarative_base()

class SensorData(BaseModel):
    id: int = Field(..., title="Reading ID")
    moisture: float = Field(..., title="Moisture Level")
    temperature: float = Field(..., title="Temperature")
    plant_id: int = Field(..., title="Plant ID")
    created_at: datetime = Field(default_factory=lambda: datetime.now(TIMEZONE))

    class Config:
        from_attributes = True

class SensorDataDB(Base):
    """Database model for sensor data.
    This model represents the sensor readings for a plant, including moisture and temperature levels. 
    It is linked to the Plant model through a foreign key relationship.
    """
    __tablename__ = "sensor_data"

    id = Column(Integer, primary_key=True, index=True)
    moisture = Column(Float, nullable=False)
    temperature = Column(Float, nullable=False)
    plant_id = Column(Integer, ForeignKey("plants.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now(TIMEZONE), nullable=False)

    @classmethod
    def get_latest_reading(cls, db_session, plant_id: int) -> Optional[SensorData]:
        """Retrieves the latest sensor reading for a given plant.
        Args:
            db_session: SQLAlchemy session object
            plant_id ID of the plant to retrieve the latest reading for
        Returns:
            Latest sensor reading for the plant if found, else None
        """
        if DEVELOPMENT_MODE:
            # For development purposes, return a mock reading
            return SensorData(
                id=1,
                moisture=20.0,
                temperature=15.0,
                plant_id=plant_id,
                created_at=datetime.now(TIMEZONE)
            )
        try:
            result = db_session.query(cls)\
                .filter(cls.plant_id == plant_id)\
                .order_by(desc(cls.created_at))\
                .first()
            if result:
                return SensorData.model_validate(result)
        except Exception as e:
            print(f"Error retrieving latest reading for plant {plant_id}: {e}")

    @classmethod
    def get_historical_readings(cls, db_session, plant_id: int, last_n_days: int = 7) -> pd.DataFrame:
        """Retrieves historical sensor readings for a given plant over the last n days.
        Args:
            db_session: SQLAlchemy session object
            plant_id ID of the plant to retrieve historical readings for
            last_n_days Number of days to look back for historical readings
        Returns:
            DataFrame containing historical sensor readings with date, moisture, and temperature
        """
        try:
            lookback = datetime.utcnow() - timedelta(days=last_n_days)
            readings = db_session.query(cls)\
                .filter(
                    cls.plant_id == plant_id,
                    cls.created_at >= lookback
                )\
                .order_by(cls.created_at)\
                .all()

            if not readings:
                return pd.DataFrame(columns=['date', 'moisture', 'temperature'])
                
            try:
                df = pd.DataFrame([{
                    'created_at': reading.created_at,
                    'moisture': reading.moisture,
                    'temperature': reading.temperature
                } for reading in readings])
                
                df['created_at'] = df['created_at'].dt.date
                result = df.groupby('created_at').agg({
                    'moisture': ['first'],
                    'temperature': ['first']
                }).reset_index()
                return result
            except (AttributeError, ValueError, KeyError) as e:
                print(f"Error processing sensor data: {e}")
                return pd.DataFrame(columns=['created_at', 'moisture', 'temperature'])
                
        except Exception as e:
            print(f"Error retrieving historical readings: {e}")
            return pd.DataFrame(columns=['created_at', 'moisture', 'temperature'])


