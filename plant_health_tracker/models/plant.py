from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional, ClassVar
import logging

from plant_health_tracker.config.base import USE_MOCKS
from plant_health_tracker.models.base import Base
class Plant(BaseModel):
    id: int = Field(..., title="Plant ID", description="Unique identifier for the plant")
    name: str = Field(..., title="Plant Name", description="Name of the plant")
    species: str = Field(..., title="Plant Species", description="Species of the plant")
    persona: str = Field(..., title="Plant Persona", description="Persona of the plant")
    personality: str = Field(..., title="Plant Personality", description="Personality traits of the plant")
    location: Optional[str] = Field('living room', title="Location", description="Location of the plant in the house")
    moisture_threshold: Optional[int] = Field(50, title="Moisture Threshold", description="Ideal moisture level for the plant")

    class Config:
        from_attributes = True

class PlantDB(Base):
    """Database model for plants."""
    __tablename__ = "plants"
    __table_args__ = {'extend_existing': True}
    
    # Set module name explicitly to avoid registry conflicts
    __module__ = "plant_health_tracker.models.plant"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    species = Column(String, nullable=False)
    persona = Column(String, nullable=False, default='little kid 7 years of age')
    personality = Column(String, nullable=False, default='cheerful, energetic, motivational')
    location = Column(String, nullable=True, default='living room')
    moisture_threshold = Column(Integer, nullable=True, default=50)

    # Update relationship to use fully qualified string reference
    sensor_readings = relationship("plant_health_tracker.models.sensor_data.SensorDataDB", back_populates="plant", 
                                 cascade="all, delete-orphan", lazy="dynamic")

    def __repr__(self):
        return f"<Plant(id={self.id}, name='{self.name}', species='{self.species}')>"
    
    @classmethod
    def get_plant(cls, id) -> Optional[Plant]:
        """Retrieves a plant by its ID from the database.

        Args:
            db_session: SQLAlchemy session object
            id (int): ID of the plant to retrieve

        Returns:
            Optional[Plant]: Plant object if found, else None
        """
        if USE_MOCKS:
            from plant_health_tracker.mock.plant_data import MockPlantDB
            return MockPlantDB().get_plant(id)
        try:
            from plant_health_tracker.db import DatabaseConnection
            db = DatabaseConnection()
            db_session = db.get_session()
            result = db_session.query(cls).filter(cls.id == id).first()
            if result:
                return Plant.model_validate(result)
            return None
        except Exception as e:
            print(f"Error retrieving plant with ID {id}: {e}")
            return None

    @classmethod
    def get_plant_list(cls) -> list[dict]:
        """Retrieves all plants' IDs and names from the database.

        Args:
            db_session: SQLAlchemy session object

        Returns:
            list[dict]: List of dictionaries containing plant IDs and names
        """
        if USE_MOCKS:
            from plant_health_tracker.mock.plant_data import MockPlantDB
            return MockPlantDB().get_plant_list()
        try:
            from plant_health_tracker.db import DatabaseConnection
            db = DatabaseConnection()
            db_session = db.get_session()
            results = db_session.query(PlantDB.id, PlantDB.name).all()
            return [{"id": result.id, "name": result.name} for result in results]
        except Exception as e:
            print(f"Error retrieving plants: {e}")
            return []


