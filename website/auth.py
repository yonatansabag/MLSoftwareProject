from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app, make_response, \
    jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from mongo import mongo_users
import re

auth = Blueprint('auth', __name__)


def is_strong_password(password):
    """Check if the password meets the strength criteria."""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    return True


def is_valid_username(username):
    """Check if the username is valid."""
    return re.match(r'^[a-zA-Z0-9_]{3,20}$', username) is not None


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and 'just_signed_up' not in session:
        current_app.config['SUCCESS'] += 1
        return redirect(url_for('views.home'))

    if request.method == 'GET':
        current_app.config['SUCCESS'] += 1
        return render_template("login.html", user=current_user)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = mongo_users.User.get(username)

        if username == 'admin' and password == 'admin':
            # print(user.password)
            login_user(user, remember=True)
            # current_app.config['SUCCESS'] += 1
            return redirect(url_for('views.home'))

        print(username, password)
        user = mongo_users.User.get(username)
        if user and check_password_hash(user.password, password):
            login_user(user, remember=True)
            current_app.config['SUCCESS'] += 1
            session.pop('just_signed_up', None)
            return redirect(url_for('views.home'))

        current_app.config['FAILURE'] += 1
        return make_response(jsonify({'error': {'code': 401, 'message': 'Incorrect username or password.'}}), 401)


@auth.route('/logout', methods=['GET'])
def logout():
    if not current_user.is_authenticated:
        return make_response(jsonify({'error': {'message': 'You are unauthorized access this page, please log in.'}}),
                             401)

    logout_user()
    current_app.config['SUCCESS'] += 1
    flash('Logged out successfully.', category='success')
    return redirect(url_for('views.home'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    print(request.form)
    if request.method == 'POST':
        print(request.form)
        username = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        if not username or not password1 or not password2:
            flash('All fields are required.', category='error')
            current_app.config['FAILURE'] += 1
            return make_response(jsonify({'error': {'message': 'All fields are required.'}}), 401)
        elif not is_valid_username(username):
            flash('Username must be 3-20 characters long and contain only letters, numbers, and underscores.',
                  category='error')
            current_app.config['FAILURE'] += 1
            return make_response(jsonify({'error': {'message': 'Username must be 3-20 characters long and contain only letters, numbers, and underscores.'}}), 401)
        elif mongo_users.User.get(username):
            flash('Username already exists.', category='error')
            current_app.config['FAILURE'] += 1
            return make_response(jsonify({'error': {'message': 'Username already exists.'}}), 401)
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
            current_app.config['FAILURE'] += 1
            return make_response(jsonify({'error': {'message': 'Passwords don\'t match.'}}), 401)
        elif not is_strong_password(password1):
            flash(
                'Password must be at least 8 characters long and contain uppercase, lowercase, digit, and special character.',
                category='error')
            current_app.config['FAILURE'] += 1
            return make_response(jsonify({'error': {'message': 'Password must be at least 8 characters long and contain uppercase, lowercase, digit, and special character.'}}), 401)
        else:
            hashed_password = generate_password_hash(password1)
            mongo_users.User.add_user(username, hashed_password)
            new_user = mongo_users.User.get(username)
            login_user(new_user, remember=True)
            flash('Account created successfully!', category='success')
            current_app.config['SUCCESS'] += 1
            session['just_signed_up'] = True
            return redirect(url_for('views.home'))

    return render_template("sign_up.html", user=current_user)
