from pymongo import MongoClient
from flask_login import UserMixin

# Initialize MongoDB client and database (global)
client = MongoClient('mongodb://localhost:27017/')
db = client['Users']
collection = db['Users']

class User(UserMixin):
    """
    Represents a user in the MongoDB database.
    """

    def __init__(self, username=None, password=None):

        self.username = username
        self.password = password

    @classmethod
    def get(cls, user_name):
        """
        Fetch a user by ID from the MongoDB database.

        Args:
            user_id (str): The ID of the user to fetch.

        Returns:
            User: The user object if found, otherwise None.
        """
        user_data = collection.find_one({"username": user_name})
        if user_data:
            return cls(username=user_data['username'], password=user_data['password'])
        return None

    @classmethod
    def add_user(cls, username, password):
        """
        Create a new user in the MongoDB database.

        Args:
            username (str): The user's username.
            password (str): The user's password.

        Returns:
            User: The newly created user object.
        """

        user_document = {
            'username': username,
            'password': password
        }
        collection.insert_one(user_document)
        return cls(username=username, password=password)
    
    
    def get_id(self):
        """
        Return the unique identifier for the user. Flask-Login uses this method
        to retrieve the user's ID.

        Returns:
            str: The user's username as the unique identifier.
        """
        return self.username
