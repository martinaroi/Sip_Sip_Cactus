from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base
from pydantic import BaseModel, Field
from typing import Optional

from plant_health_tracker.config.base import DEVELOPMENT_MODE

Base = declarative_base()

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

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    species = Column(String, nullable=False)
    persona = Column(String, nullable=False, default='little kid 7 years of age')
    personality = Column(String, nullable=False, default='cheerful, energetic, motivational')
    location = Column(String, nullable=True, default='living room')
    moisture_threshold = Column(Integer, nullable=True, default=50)

    def __repr__(self):
        return f"<Plant(id={self.id}, name='{self.name}', species='{self.species}')>"
    
    def get_plant(self, db_session, id) -> Optional[Plant]:
        """Retrieves a plant by its ID from the database.

        Args:
            db_session: SQLAlchemy session object
            id (int): ID of the plant to retrieve

        Returns:
            Optional[Plant]: Plant object if found, else None
        """
        if DEVELOPMENT_MODE:
            from ..mock.plant_data import MockPlantDB
            return MockPlantDB().get_plant(db_session, id)
        try:
            result = db_session.query(self).filter(self.id == id).first()
            if result:
                return Plant.model_validate(result)
            return None
        except Exception as e:
            print(f"Error retrieving plant with ID {id}: {e}")
            return None



