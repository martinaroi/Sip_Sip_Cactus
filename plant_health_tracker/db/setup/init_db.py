import logging
from typing import Optional
from sqlalchemy import inspect

from plant_health_tracker.db.database import DatabaseConnection
from plant_health_tracker.models.base import Base
from plant_health_tracker.models.plant import PlantDB
from plant_health_tracker.models.sensor_data import SensorDataDB
from plant_health_tracker.mock.plant_data import PLANT_MOCK_A, PLANT_MOCK_B

logger = logging.getLogger(__name__)

def populate_initial_data(db_session) -> Optional[Exception]:
    """Populate the database with initial mock data.
    
    Args:
        db_session: SQLAlchemy session object
    
    Returns:
        Optional[Exception]: Returns Exception if population fails, None otherwise.
    """
    try:
        # Check if plants already exist
        existing_plants = db_session.query(PlantDB).all()
        if existing_plants:
            logger.info("Database already contains plants. Skipping population.")
            return None

        # Create PlantDB instances from mock data
        plants = [
            PlantDB(**PLANT_MOCK_A.model_dump()),
            PlantDB(**PLANT_MOCK_B.model_dump())
        ]

        db_session.add_all(plants)
        db_session.commit()
        logger.info("Successfully populated database with initial data")
        return None

    except Exception as e:
        logger.error(f"Error populating database: {e}")
        db_session.rollback()
        return e

def init_database(drop_existing: bool = False) -> Optional[Exception]:
    """Initialize the database tables and populate with initial data if empty.

    Args:
        drop_existing (bool): If True, drops all existing tables before creating new ones.

    Returns:
        Optional[Exception]: Returns Exception if initialization fails, None otherwise.
    """
    try:
        db = DatabaseConnection()
        engine = db.get_engine()

        logger.info("Tables to be created: %s", Base.metadata.tables.keys())

        if drop_existing:
            logger.info("Dropping all existing tables...")
            Base.metadata.drop_all(bind=engine)

        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        
        # Verify tables were created
        inspector = inspect(engine)
        created_tables = inspector.get_table_names()
        logger.info("Created tables: %s", created_tables)
        
        if not created_tables:
            raise Exception("No tables were created")

        logger.info("Database initialization completed successfully.")

        # Always check for empty tables and populate if needed
        session = db.get_session()
        try:
            if error := populate_initial_data(session):
                return error
        finally:
            session.close()

        return None

    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        return e

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize the database
    if error := init_database(drop_existing=True):
        logger.error(f"Database initialization failed: {error}")
        exit(1)
    logger.info("Database Setup completed successfully.")
