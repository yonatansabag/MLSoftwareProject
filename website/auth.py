from flask import Blueprint, jsonify, make_response, render_template, request, flash, redirect, url_for, session, current_app
from .models import User
from werkzeug.security import generate_password_hash, check_password_hash
from .app import db   # Assuming .app imports the db instance
from flask_login import login_user, login_required, logout_user, current_user, UserMixin
from .utils import DummyUser

auth = Blueprint('auth', __name__)



@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login functionality.

    GET:
        Renders the 'login.html' template if user is not authenticated.
        Redirects to 'views.upload_image' if user is already authenticated and not just signed up.

    POST:
        Validates user credentials:
            - Retrieves username and password from form data.
            - Queries the database for a user with the provided username.
            - Compares the hashed password with the stored hash in the database.
            - Logs in the user using Flask-Login if credentials are correct.
            - Removes 'just_signed_up' session variable upon successful login.
        Increments 'SUCCESS' counter in the current app configuration upon successful login attempt.
        Returns a JSON response with 'is_authenticated' set to False and HTTP status 401 if login fails.

    Returns:
        Response: Renders 'login.html' template (GET) or redirects to 'views.upload_image' or returns JSON response (POST).
    """
    if current_user.is_authenticated and 'just_signed_up' not in session:
        return redirect(url_for('views.upload_image'))  # Redirect to the upload image page if already logged in

    if request.method == 'GET':
        return render_template("login.html", user=current_user)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Check for admin credentials
        if username == 'admin' and password == 'admin':
            admin_user = DummyUser(id=0, email='admin')
            login_user(admin_user, remember=True)
            current_app.config['SUCCESS'] += 1
            session.pop('just_signed_up', None)
            return redirect(url_for('views.upload_image'))

        user = User.query.filter_by(email=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user, remember=True)
            current_app.config['SUCCESS'] += 1
            session.pop('just_signed_up', None)
            return redirect(url_for('views.upload_image'))

        current_app.config['FAILURE'] += 1
        return make_response(jsonify({'is_authenticated': False}), 401)

@auth.route('/logout', methods=['GET'])
@login_required
def logout():
    """
    Handles user logout functionality.

    Logs out the current user using Flask-Login.
    Increments 'SUCCESS' counter in the current app configuration.
    Redirects to 'views.home' after successful logout.

    Returns:
        Redirect: Redirects to 'views.home'.
    """
    logout_user()
    current_app.config['SUCCESS'] += 1
    return redirect(url_for('views.home'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    """
    Handles user sign-up functionality.

    POST:
        Validates user input:
            - Checks if the provided email already exists in the database.
            - Checks if the username (email) is empty.
            - Checks if the passwords match and are not empty.
        Creates a new user if input is valid:
            - Hashes the password using generate_password_hash().
            - Adds the new user to the database and commits the transaction.
            - Logs in the new user using Flask-Login.
            - Flashes a success message and increments 'SUCCESS' counter.
            - Sets 'just_signed_up' session variable to True and redirects to 'auth.login'.

    Returns:
        Response: Renders 'sign_up.html' template (GET) or redirects to 'auth.login' (POST).
    """
    if request.method == 'POST':
        username = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by(email=username).first()
        if user:
            flash('Username already exists.', category='error')
            current_app.config['FAILURE'] += 1
        elif username == '':
            flash('Username is empty.', category='error')
            current_app.config['FAILURE'] += 1
        elif password1 == '':
            flash('Password is empty.', category='error')
            current_app.config['FAILURE'] += 1
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
            current_app.config['FAILURE'] += 1
        else:
            new_user = User(email=username, password=generate_password_hash(password1))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            current_app.config['SUCCESS'] += 1
            session['just_signed_up'] = True
            return redirect(url_for('auth.login'))

    current_app.config['SUCCESS'] += 1
    return render_template("sign_up.html", user=current_user)
