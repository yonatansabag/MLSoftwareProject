import json
import unittest
import requests
from mongo import mongo_users
from unittest.mock import patch


class AuthTest(unittest.TestCase):
    """
    Test suite for the Authentication API.
    This suite tests the login, logout, and sign-up functionality.
    """

    def setUp(self):
        """
        Set up test variables and URLs.
        This method runs before each test case.
        """
        self.base_url = 'http://127.0.0.1:8000/'
        self.login_data = {"username": "admin", "password": "admin"}
        self.signup_data = {
            'email': 'new_user12324234643',
            'password1': 'Password1!',
            'password2': 'Password1!'
        }

    def _resp_is_json(self, response):
        """Helper method to check if response is JSON."""
        self.assertEqual("application/json", response.headers.get("Content-Type", ""))

    def _login(self):
        """Helper method to log in a user and return the response."""
        return requests.post(self.base_url + 'login', data=self.login_data, allow_redirects=False)

    def test_login_correct_info(self):
        """Test logging in with correct username and password."""
        response = self._login()
        self.assertEqual(302, response.status_code)  # Redirect on successful login

    def test_login_incorrect_password(self):
        """Test logging in with correct username but incorrect password."""
        login_data_incorrect_password = {'username': 'admin', 'password': 'wrongpassword'}
        response = requests.post(self.base_url + 'login', data=login_data_incorrect_password)
        self._resp_is_json(response)
        self.assertEqual(401, response.status_code)
        self.assertIn('Incorrect username or password.', response.json()['error']['message'])

    def test_login_non_exists_user(self):
        """Test logging in with non-existent username."""
        login_data_non_existent_user = {'username': 'nonexistent', 'password': 'admin'}
        response = requests.post(self.base_url + 'login', data=login_data_non_existent_user)
        self._resp_is_json(response)
        self.assertEqual(401, response.status_code)
        self.assertIn('Incorrect username or password.', response.json()['error']['message'])

    def test_logout_without_being_logged_in(self):
        """Test logging out without being logged in."""
        logout_response = requests.get(self.base_url + "logout")
        self._resp_is_json(logout_response)
        self.assertEqual(401, logout_response.status_code)
        self.assertIn('You are unauthorized access this page, please log in.',
                      logout_response.json()['error']['message'])

    def test_logout(self):
        """Test logging out after a successful login."""
        login_response = self._login()
        self.assertEqual(302, login_response.status_code)

        logout_response = requests.get(self.base_url + "logout", cookies=login_response.cookies, allow_redirects=False)
        self.assertEqual(302, logout_response.status_code)  # Redirect on logout

    def test_signup_existing_username(self):
        """Test signing up with a username that already exists."""
        existing_user_data = {
            'email': 'admin',
            'password1': 'Aa1234567!',
            'password2': 'Aa1234567!'
        }
        response = requests.post(self.base_url + 'sign-up', data=existing_user_data)
        self._resp_is_json(response)
        self.assertEqual(401, response.status_code)
        self.assertIn('Username already exists.', response.json()['error']['message'])

    def test_signup_unmatched_passwords(self):
        """Test signing up with unmatched passwords."""
        signup_data_unmatched_passwords = {
            'email': 'new_user2',
            'password1': 'Password1!',
            'password2': 'Password2!'
        }
        response = requests.post(self.base_url + 'sign-up', data=signup_data_unmatched_passwords)
        self._resp_is_json(response)
        self.assertEqual(401, response.status_code)
        self.assertIn('Passwords don\'t match.', response.json()['error']['message'])

    def test_signup_weak_password(self):
        """Test signing up with a weak password."""
        weak_password_data = self.signup_data.copy()
        weak_password_data['email'] = 'weak_password'
        weak_password_data['password1'] = 'weak'
        weak_password_data['password2'] = 'weak'
        response = requests.post(self.base_url + 'sign-up', data=weak_password_data)
        self._resp_is_json(response)
        self.assertEqual(401, response.status_code)
        self.assertIn(
            'Password must be at least 8 characters long and contain uppercase, lowercase, digit, and special character.',
            response.json()['error']['message'])

    def test_successful_signup_and_login(self):
        """Test signing up with valid data and then logging in."""
        existing_user = mongo_users.User.get(self.signup_data['email'])
        if existing_user:
            mongo_users.delete_user(existing_user.username)
        response_signup = requests.post(
            self.base_url + 'sign-up',
            data=self.signup_data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            allow_redirects=False
        )

        if response_signup.status_code != 302:
            print("Signup response:", response_signup.text)  # Log the response for debugging

        self.assertEqual(302, response_signup.status_code)  # Redirect on successful signup

        # Proceed with login only if signup is successful
        if response_signup.status_code == 302:
            login_response = requests.post(
                self.base_url + 'login',
                data={'username': self.signup_data['email'], 'password': self.signup_data['password1']},
                cookies=response_signup.cookies,
                allow_redirects=False
            )
            self.assertEqual(302, login_response.status_code)


if __name__ == "__main__":
    unittest.main()
