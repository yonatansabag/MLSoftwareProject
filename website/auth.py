from flask import Blueprint, jsonify, make_response, render_template, request, flash, redirect, url_for, session, \
    current_app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user, UserMixin
from mongo import mongo_users  # Import the User class that interacts with MongoDB

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and 'just_signed_up' not in session:
        return redirect(url_for('views.home'))

    if request.method == 'GET':
        return render_template("login.html", user=current_user)

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = mongo_users.User.get(username)

        if username == 'admin' and password == 'admin':
            print(user.password)
            login_user(user, remember=True)
            return redirect(url_for('views.home'))

        print(username, password)
        user = mongo_users.User.get(username)
        if user and check_password_hash(user.password, password):
            login_user(user, remember=True)
            current_app.config['SUCCESS'] += 1
            session.pop('just_signed_up', None)
            return redirect(url_for('views.home'))

        current_app.config['FAILURE'] += 1
        return make_response(jsonify({'is_authenticated': False}), 401)


@auth.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    current_app.config['SUCCESS'] += 1
    return redirect(url_for('views.home'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        username = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = mongo_users.User.get(username)
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
            hashed_password = generate_password_hash(password1)
            mongo_users.User.add_user(username, hashed_password)
            new_user = mongo_users.User.get(username)  # Fetch the newly created user
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            current_app.config['SUCCESS'] += 1
            session['just_signed_up'] = True
            return redirect(url_for('auth.login'))

    current_app.config['SUCCESS'] += 1
    return render_template("sign_up.html", user=current_user)
