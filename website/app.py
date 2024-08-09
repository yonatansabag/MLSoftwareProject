import time
from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_login import LoginManager, current_user
from pymongo import MongoClient
from os import path
import sys
import os
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mongo')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', "mongo")))
# Import MongoDB configuration
from mongo.mongo_users import game, User


from werkzeug.security import generate_password_hash

def initialize_default_admin():
    """
    Creates a default admin user if it does not already exist.

    Returns:
        None
    """
    admin_username = 'admin'
    admin_password = 'admin'
    
    # Check if admin user already exists
    if User.get(admin_username) is None:
        # Create the admin user
        User.add_user(admin_username, admin_password)
        print(f"Default admin user '{admin_username}' created.")
    else:
        print(f"Admin user '{admin_username}' already exists.")

def create_app():
    """
    Creates and configures the Flask application.

    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'  # Secret key for session management
    app.config['SUCCESS'] = 0  # Counter for successful operations
    app.config['FAILURE'] = 0  # Counter for failed operations
    app.config['START_TIME'] = time.time()  # Application start time
    
    # Initialize Flask-Login for managing user sessions
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    from .views import views
    from .auth import auth

    # Register blueprints for different parts of the application
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    @login_manager.user_loader
    def load_user(user_id):
        """
        Callback function for reloading a user object from the user ID stored in the session.

        Args:
            user_id (str): ID of the user to load.

        Returns:
            User: User object corresponding to the user ID.
        """
        return User.get(user_id)  # Adjust this if necessary to fetch the user by ID

    @app.context_processor
    def inject_user():
        """
        Injects the current user object into all templates.

        Returns:
            dict: Dictionary with the 'user' key set to the current user object.
        """
        return dict(user=current_user)
    
    @login_manager.unauthorized_handler
    def unauthorized_callback():
        """
        Handles unauthorized access attempts.

        Returns:
            Any: JSON response with an unauthorized error message and HTTP status code 401.
        """
        return make_response(jsonify({'error': {'code': 401, 'message': 'You are unauthorized to access that page, please log in.'}}), 401)
    
    @app.route('/')
    def index():
        """
        Serves the index.html file from the root directory.

        Returns:
            str: Contents of index.html file.
        """
        return send_from_directory('.', 'index.html')
    initialize_default_admin()
    game.drop()
    return app




