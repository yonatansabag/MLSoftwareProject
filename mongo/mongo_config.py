from pymongo import MongoClient

MONGO_URI = 'mongodb://localhost:27017/'  # Adjust this URI as needed
client = MongoClient(MONGO_URI)
db = client['Users']
