from ..models.plant import Plant

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
