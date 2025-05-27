# from pymongo import MongoClient
# from dotenv import load_dotenv
# import os

# # Load environment variables from .env file
# load_dotenv()

# # Get the MongoDB URI from environment variables
# MONGO_URI = os.getenv("MONGO_URI")

# # Establish the MongoDB connection
# try:
#     client = MongoClient(MONGO_URI)
#     db = client["callaway_ai"] 
#     db["users"].create_index("id", unique=True)
#     print("MongoDB connection established successfully.")
# except Exception as e:
#     print(f"Failed to connect to MongoDB: {e}")

from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

try:
    client = MongoClient(MONGO_URI)
    db = client["callaway_ai"]

    # Get users collection and export it
    users_collection = db["users"]

    # Create index only if necessary
    existing_indexes = users_collection.index_information()
    if "custom_id_index" not in existing_indexes:
        users_collection.create_index([("id", 1)], name="custom_id_index", unique=True)

    print("MongoDB connection established successfully.")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}") 