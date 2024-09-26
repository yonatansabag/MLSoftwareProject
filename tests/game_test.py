import unittest
import requests
import time

PORT = 8000

class WordGuessGameAPITest(unittest.TestCase):

    def setUp(self):
        """Set up test variables and URLs."""
        self.base_url = f'http://127.0.0.1:{PORT}/'
        self.login_data = {"username": "admin", "password": "admin"}
        self.session = requests.Session()  # Ensure we use the same session for requests

    def _resp_is_json(self, response):
        """Helper method to check if response is JSON."""
        self.assertEqual("application/json", response.headers.get("Content-Type", ""))

    def _login(self):
        """Helper method to log in a user and return the response."""
        return self.session.post(self.base_url + 'login', data=self.login_data, allow_redirects=False)

    def test_login_correct_info(self):
        """Test logging in with correct username and password."""
        response = self._login()
        self.assertEqual(200, response.status_code)  # Redirect on successful login

    def test_start_game(self):
        """Test starting the game."""
        # Log in first
        login_response = self._login()
        self.assertEqual(200, login_response.status_code)  # Ensure login was successful
        
        # Now make the request to start the game using the same session
        response = self.session.post(self.base_url + 'game')
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("Content-Type", ""))

    def test_create_room_with_multiple_players(self):
        """Test creating a room with more than one player."""
        room_data = {
            "name": "TestRoom",
            "num_players": 3,
            "create": "Create Room"
        }
        login_response = self._login()
        waiting_room_response = self.session.post(self.base_url + 'roomjoin', data=room_data)
        self.assertEqual(waiting_room_response.status_code, 200)
        # Check for key content in the waiting room response
        self.assertIn("Waiting for Everyone to Enter the Room", waiting_room_response.text)
        self.assertIn("Room Code:", waiting_room_response.text)
        self.assertIn("Please be patient while we wait for all players to join.", waiting_room_response.text)
        
    def test_create_room_with_no_name(self):
        """Test creating a room with no name."""
        room_data = {
            "name": "",
            "num_players": 3,
            "create": "Create a Room"
        }
        login_response = self._login()
        room_response = self.session.post(self.base_url + 'roomjoin', data=room_data)
        self.assertEqual(room_response.status_code, 200)
        # Check for key content in the waiting room response
        self.assertIn("Create a Room", room_response.text)
        self.assertIn("Join a Room", room_response.text)
        
    def test_create_room_with_one_players(self):
        """Test creating a room with one player."""
        room_data = {
            "name": "TestRoom",
            "num_players": 1,
            "create": "Create a Room"
        }
        login_response = self._login()
        game_response = self.session.post(self.base_url + 'roomjoin', data=room_data)
        time.sleep(10)
        game_response = self.session.post(self.base_url + 'game')
        self.assertEqual(game_response.status_code, 200)
        self.assertIn('Word Guess Game', game_response.text)
    
    def test_join_room_with_no_code(self):
        """Test joining a room with no code."""
        room_data = {
            "name": "TestRoom",
            "room code:": "",
            "join": "Join a Room"
        }
        login_response = self._login()
        room_response = self.session.post(self.base_url + 'roomjoin', data=room_data)

        self.assertEqual(room_response.status_code, 200)
        # Check for key content in the waiting room response
        self.assertIn("Create a Room", room_response.text)
        self.assertIn("Join a Room", room_response.text)
        
    def test_submit_guess(self):
        """Test submitting a guess in the game."""
        # Step 1: Create a room and start the game
        room_data = {
            "name": "TestRoom",
            "num_players": 1,
            "create": "Create a Room"
        }
        
        login_response = self._login()
        game_response = self.session.post(self.base_url + 'roomjoin', data=room_data)
        
        # Wait and verify the game page is loaded
        time.sleep(10)
        game_response = self.session.post(self.base_url + 'game')
        self.assertEqual(game_response.status_code, 200)
        
        # Step 2: Prepare the guess data
        guess_data = {
            "guess": "example",  # Replace with the actual guess you want to test
            "submit": "Submit Guess"
        }
        
        # Step 3: Submit the guess
        guess_response = self.session.post(self.base_url + 'game', data=guess_data)
        
        # Step 4: Verify the response       
        self.assertEqual(guess_response.status_code, 200)
        

if __name__ == "__main__":
    unittest.main()
