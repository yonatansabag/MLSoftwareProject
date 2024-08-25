from pymongo import MongoClient
from flask_login import UserMixin

# Initialize MongoDB client and database (global)
client = MongoClient('mongodb://localhost:27017/')
db_users = client['Users']
db_words = client['Words']
db_guesses = client['Guess']
collection = db_users['Users']
game = db_words["Words"]
guesses = db_guesses['Guess']


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


class WordDatabase():
    """
    Represents a word in the MongoDB database.
    """

    def __init__(self, word=None):
        self.word = word

    @classmethod
    def get(cls, word):
        word_data = game.find_one({"word": word})
        if word_data:
            return cls(word=word_data['word'])
        return None

    @classmethod
    def add_word(cls, word):
        word_doc = {
            'word': word,
        }
        game.insert_one(word_doc)
        return cls(word=word)

    def get_id(self):
        return self.word


class GuessesDatabase():
    """
    Represents a word in the MongoDB database.
    """

    def __init__(self, guess=None, score=None):
        self.guess = guess
        self.score = score

    @classmethod
    def add_word(cls, guess, score):
        word_doc = {
            'guess': guess,
            'score': score
        }
        guesses.insert_one(word_doc)
        return cls(guess=guess, score=score)

    def get_id(self):
        return self.guess

    @classmethod
    def print_all(cls):
        """
        Prints all documents in the MongoDB collection.
        """
        # Fetch all documents from the collection
        all_documents = list(guesses.find({}))
        # Print each document
        result = [{'guess': doc.get('guess'), 'score': doc.get('score')} for doc in all_documents]
        # print(result)
        return result
