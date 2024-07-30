import time
from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import google.generativeai as genai
from google.generativeai.types import ContentType
from PIL import Image
import os
from flask_login import LoginManager, current_user
from typing import Any
from os import path
from .utils import DummyUser
from celery_config import make_celery

# Initialize SQLAlchemy database instance


db = SQLAlchemy()
DB_NAME = "database.db"

# Define the upload folder for file storage
UPLOAD_FOLDER = 'uploads'


def create_app():
    """
    Creates and configures the Flask application.

    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'  # Secret key for session management
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'  # SQLite database URI
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # Upload folder for file storage
    app.config['SUCCESS'] = 0  # Counter for successful operations
    app.config['FAILURE'] = 0  # Counter for failed operations
    app.config['START_TIME'] = time.time()  # Application start time
    app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
    app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
    db.init_app(app)  # Initialize SQLAlchemy with the app instance
    celery = make_celery(app)

    from .views import views
    from .auth import auth

    # Register blueprints for different parts of the application
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User
    
    with app.app_context():
        db.create_all()  # Create all database tables if they do not exist

    # Initialize Flask-Login for managing user sessions
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        """
        Callback function for reloading a user object from the user ID stored in the session.

        Args:
            user_id (str): ID of the user to load.

        Returns:
            User: User object corresponding to the user ID.
        """
        if user_id == "0":  # Check for admin user
            return DummyUser(id=0, email='admin')
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_user():
        """
        Injects the current user object into all templates.

        Returns:
            dict: Dictionary with the 'user' key set to the current user object.
        """
        return dict(user=current_user)
    
    @login_manager.unauthorized_handler
    def unauthorized_callback() -> Any:
        """
        Handles unauthorized access attempts.

        Returns:
            Any: JSON response with an unauthorized error message and HTTP status code 401.
        """
        return make_response(jsonify({'error': {'code': 401, 'message': 'You are unauthorized to access that page, please log in.'}}), 401)
    
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)  # Create the upload folder if it does not exist

    @app.route('/')
    def index():
        """
        Serves the index.html file from the root directory.

        Returns:
            str: Contents of index.html file.
        """
        return send_from_directory('.', 'index.html')

    return app

def create_database(app):
    """
    Creates the database tables if they do not exist.

    Args:
        app (Flask): The Flask application instance.

    Returns:
        None
    """
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)  # Create all database tables if they do not exist
