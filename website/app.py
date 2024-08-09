# import time
# from flask import Flask, request, jsonify, send_from_directory, make_response
# from flask_sqlalchemy import SQLAlchemy
# from werkzeug.utils import secure_filename
# import google.generativeai as genai
# from google.generativeai.types import ContentType
# from PIL import Image
# import os
# from flask_login import LoginManager, current_user
# from typing import Any
# from os import path
# import sys
# # from .utils import DummyUser
# from pymongo import MongoClient
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mongo')))
# from mongo_config import results_collection, db

# # DB_NAME = "database.db"
# # # MongoDB setup
# # MONGO_URI = 'mongodb://localhost:27017/'  # Use the service name 'mongo' as defined in Docker Compose
# # # MONGO_URI ='mongodb://mongo:27017/'
# # client = MongoClient(MONGO_URI)
# # db = client['Users']  
# # results_collection = db['Users']
# # # Define the upload folder for file storage
# # UPLOAD_FOLDER = 'uploads'


# def create_app():
#     """
#     Creates and configures the Flask application.

#     Returns:
#         Flask: Configured Flask application instance.
#     """
#     app = Flask(__name__)
#     app.config['SECRET_KEY'] = 'hjshjhdjah kjshkjdhjs'  # Secret key for session management
#     app.config['SUCCESS'] = 0  # Counter for successful operations
#     app.config['FAILURE'] = 0  # Counter for failed operations
#     app.config['START_TIME'] = time.time()  # Application start time
#     app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
#     app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
#     # db.init_app(app)  # Initialize SQLAlchemy with the app instance
    
#     from .views import views
#     from .auth import auth

#     # Register blueprints for different parts of the application
#     app.register_blueprint(views, url_prefix='/')
#     app.register_blueprint(auth, url_prefix='/')

#     # from .models import User
    
#     # with app.app_context():
#     #     db.create_all()  # Create all database tables if they do not exist

#     # Initialize Flask-Login for managing user sessions
#     login_manager = LoginManager()
#     login_manager.login_view = 'auth.login'
#     login_manager.init_app(app)

#     @login_manager.user_loader
#     def load_user(user_id):
#         """
#         Callback function for reloading a user object from the user ID stored in the session.

#         Args:
#             user_id (str): ID of the user to load.

#         Returns:
#             User: User object corresponding to the user ID.
#         """
#         pass
    
#     @app.context_processor
#     def inject_user():
#         """
#         Injects the current user object into all templates.

#         Returns:
#             dict: Dictionary with the 'user' key set to the current user object.
#         """
#         return dict(user=current_user)
    
#     @login_manager.unauthorized_handler
#     def unauthorized_callback() -> Any:
#         """
#         Handles unauthorized access attempts.

#         Returns:
#             Any: JSON response with an unauthorized error message and HTTP status code 401.
#         """
#         return make_response(jsonify({'error': {'code': 401, 'message': 'You are unauthorized to access that page, please log in.'}}), 401)
    
# #      os.path.exists(UPLOAD_FOLDER):
# #         os.makedirs(UPLOAD_FOLDER)  # Create the upload folder if it does not exist
# # if not
#     @app.route('/')
#     def index():
#         """
#         Serves the index.html file from the root directory.

#         Returns:
#             str: Contents of index.html file.
#         """
#         return send_from_directory('.', 'index.html')

#     return app

# def create_database(app):
#     """
#     Creates the database tables if they do not exist.

#     Args:
#         app (Flask): The Flask application instance.

#     Returns:
#         None
#     """
#     if not path.exists('website/' + db):
#         db.create_all(app=app)  # Create all database tables if they do not exist

import time
from flask import Flask, request, jsonify, send_from_directory, make_response
from flask_login import LoginManager, current_user
from pymongo import MongoClient
from os import path
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'mongo')))
# Import MongoDB configuration
from mongo_config import results_collection, db
from mongo_users import User


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
    app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
    app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
    
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
    return app


# No need for create_database function as MongoDB creates collections on the fly

