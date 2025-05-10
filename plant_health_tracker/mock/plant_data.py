from datetime import datetime, timezone
from ..models.plant import Plant

# Plant mocks - these look correct following the Plant model structure
PLANT_MOCK_A = Plant(
    id=1,
    name='Vendula',
    species='Venus flytrap',
    persona='teenage girl',
    personality='very sarcastic, dramatic and funny',
    location='living room',
    moisture_threshold=80
)

PLANT_MOCK_B = Plant(
    id=2, 
    name='Bobeš',
    species='Cactus',
    persona='old grumpy grandpa',
    personality='very grumpy, sarcastic and funny',
    location='bedroom',
    moisture_threshold=15
)

class MockPlantDB:
    def get_plant(self, db_session, id) -> Plant:
        """Retrieves a plant by its ID from the database.
        
        Args:
            db_session: SQLAlchemy session object
            id (int): ID of the plant to retrieve
        
        Returns:
            Plant: Plant object if found, else None
        """
        if id == 1:
            return PLANT_MOCK_A
        elif id == 2:
            return PLANT_MOCK_B
        else:
            return None