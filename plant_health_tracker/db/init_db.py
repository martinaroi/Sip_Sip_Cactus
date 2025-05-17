import logging
from typing import Optional
from sqlalchemy import inspect

from plant_health_tracker.db.database import DatabaseConnection, Base
from plant_health_tracker.models.plant import PlantDB
from plant_health_tracker.models.sensor_data import SensorDataDB

logger = logging.getLogger(__name__)

def init_database(drop_existing: bool = False) -> Optional[Exception]:
    """Initialize the database tables.

    Args:
        drop_existing (bool): If True, drops all existing tables before creating new ones.

    Returns:
        Optional[Exception]: Returns Exception if initialization fails, None otherwise.
    """
    try:
        db = DatabaseConnection()
        engine = db.get_engine()

        # Debug: Print all tables that will be created
        logger.info("Tables to be created: %s", Base.metadata.tables.keys())

        if drop_existing:
            logger.info("Dropping all existing tables...")
            Base.metadata.drop_all(bind=engine)

        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created using inspector
        inspector = inspect(engine)
        created_tables = inspector.get_table_names()
        logger.info("Created tables: %s", created_tables)
        
        if not created_tables:
            raise Exception("No tables were created")

        logger.info("Database initialization completed successfully.")
        return None

    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return e

if __name__ == "__main__":
    # Configure logging with more detailed format
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize the database
    error = init_database(drop_existing=True)
    if error:
        print(f"Database initialization failed: {error}")
        exit(1)
    print("Database initialization completed successfully.")
