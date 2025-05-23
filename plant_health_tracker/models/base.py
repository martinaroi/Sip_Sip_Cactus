from sqlalchemy.orm import declarative_base

# Create the declarative base with a registry that uses fully qualified paths
Base = declarative_base(name="PlantHealthBase", class_registry=dict())
