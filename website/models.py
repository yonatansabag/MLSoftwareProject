from .app import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    """
    Handles user creation in the DB and the structure of the DB.

    """
        
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))