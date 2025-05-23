from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get the MongoDB URI from environment variables
MONGO_URI = os.getenv("MONGO_URI")

# Establish the MongoDB connection
try:
    client = MongoClient(MONGO_URI)
    db = client["callaway_ai"] 
    db["users"].create_index("id", unique=True)
    print("MongoDB connection established successfully.")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")