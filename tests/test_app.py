import unittest
import requests
import os

PORT = 5000
FAST_REPLY_TIME_SEC = 20  # 5000 ms

class ImageUploadAPITest(unittest.TestCase):
    """
    Unit tests for testing the image upload API endpoints.
    """

    def setUp(self):
        """
        Setup method to initialize test environment.
        """
        print("Setting up the test...\n")
        self.base_url = f"http://localhost:{PORT}/"
        script_dir = os.path.dirname(__file__)
        self.valid_image_file = os.path.join(script_dir, '../uploads/mamix.jpeg')
        self.invalid_image_file = os.path.join(script_dir, '../uploads/Screenshot.jpe')
        self.login_data = {"username": "admin", "password": "admin"}
        self.session = requests.Session()

    def _resp_is_json(self, response):
        """
        Helper method to check if response is JSON.
        
        Args:
            response (requests.Response): Response object to check.
        """
        print("Checking if response is JSON...\n")
        self.assertEqual("application/json", response.headers.get("Content-Type", ""))

    def test_login_correct_info(self):
        """
        Test case for logging in with correct credentials.
        """
        response = requests.post(self.base_url + "login", data=self.login_data, allow_redirects=False)
        self.assertEqual(302, response.status_code)

    def test_login_wrong_username(self):
        """
        Test case for logging in with incorrect username.
        """
        print("Running test_login...\n")
        fake_login_data = {"username": "fake", "password": "admin"}
        response = requests.post(self.base_url + "login", data=fake_login_data)
        self._resp_is_json(response)
        self.assertEqual(response.status_code, 401)
    
    def test_login_wrong_password(self):
        """
        Test case for logging in with incorrect password.
        """
        print("Running test_login...\n")
        fake_login_data = {"username": "admin", "password": "fake"}
        response = requests.post(self.base_url + "login", data=fake_login_data)
        self._resp_is_json(response)
        self.assertEqual(response.status_code, 401)

    def test_get_upload_page_no_login(self):
        """
        Test case for accessing the upload page without logging in.
        """
        response = requests.get(self.base_url + 'upload_image')
        self.assertEqual(401, response.status_code)
        self._resp_is_json(response)

    def test_unauthorized_upload_try(self):
        """
        Test case for attempting to upload an image without authorization.
        """
        print("Running test_unauthorized_upload...\n")
        with open(self.valid_image_file, "rb") as image_file:
            response = requests.post(self.base_url + "upload_image", files={"file": image_file})
        self.assertEqual(response.status_code, 401)
        self.assertLess(response.elapsed.total_seconds(), FAST_REPLY_TIME_SEC)
        self._resp_is_json(response)

    def test_authorized_upload_valid_image(self):
        """
        Test case for uploading a valid image after successful login.
        """
        print("Running test_authorized_upload_valid_image...\n")
        login_response = self.session.post(self.base_url + "login", data=self.login_data, allow_redirects=False)
        self.assertEqual(302, login_response.status_code)
        
        with open(self.valid_image_file, 'rb') as img:
            response = self.session.post(self.base_url + "upload_image", files={"image": img}, cookies=login_response.cookies)
        self._resp_is_json(response)
        self.assertIn('matches', response.json())
        self.assertEqual(response.status_code, 200)
        self.assertLess(response.elapsed.total_seconds(), FAST_REPLY_TIME_SEC)

        matches = response.json()['matches']
        self.assertIsInstance(matches, list)
        for match in matches:
            self.assertIsInstance(match, dict)
            self.assertIn('name', match)
            self.assertIn('score', match)

    def test_authorized_upload_invalid_image(self):
        """
        Test case for attempting to upload an invalid image after successful login.
        """
        print("Running test_authorized_upload_invalid_image...\n")
        login_response = self.session.post(self.base_url + "login", data=self.login_data, allow_redirects=False)
        self.assertEqual(302, login_response.status_code)

        with open(self.invalid_image_file, 'rb') as img:
            response = self.session.post(self.base_url + "upload_image", files={"image": img}, cookies=login_response.cookies)
        self.assertEqual(response.status_code, 400)
        self.assertLess(response.elapsed.total_seconds(), FAST_REPLY_TIME_SEC)
        self._resp_is_json(response)

    def test_get_result_without_login(self):
        """
        Test case for accessing result endpoints without logging in.
        """
        response = requests.get(self.base_url + 'result')
        self.assertEqual(404, response.status_code)

        response = requests.get(self.base_url + 'result/777')
        self._resp_is_json(response)
        self.assertEqual(401, response.status_code)
    
    def test_get_result_with_login(self):
        """
        Test case for accessing result endpoints after logging in.
        """
        login_response = self.session.post(self.base_url + "login", data=self.login_data, allow_redirects=False)
        self.assertEqual(302, login_response.status_code)
        response = self.session.get(self.base_url + 'result', cookies=login_response.cookies)
        self.assertEqual(404, response.status_code)
        response2 = self.session.get(self.base_url + 'result/777', cookies=login_response.cookies)
        self._resp_is_json(response2)
        self.assertEqual(404, response2.status_code)

    def test_logout(self):
        """
        Test case for logging out.
        """
        login_response = self.session.post(self.base_url + "login", data=self.login_data, allow_redirects=False)
        self.assertEqual(302, login_response.status_code)
        response = self.session.get(self.base_url + 'logout', cookies=login_response.cookies, allow_redirects=False)
        self.assertEqual(302, response.status_code)

    def test_status(self):
        """
        Test case for checking application status.
        """
        response = requests.get(self.base_url + 'status')
        self.assertEqual(200, response.status_code)
        self._resp_is_json(response)

        data = response.json()
        self.assertIsInstance(data, dict)
        self.assertIn('uptime', data)
        self.assertIn('processed', data)
        self.assertIn("api_version", data)
        self.assertIn("health", data)
        processed = data['processed']
        self.assertIsInstance(processed, dict)
        self.assertIn('success', processed)
        self.assertIn('fail', processed)
        self.assertIn('running', processed)
        self.assertIn('queued', processed)

        self.assertIsInstance(data['uptime'], float)
        self.assertIsInstance(data['api_version'], (float, int))
        self.assertIsInstance(data['health'], str)
        self.assertIsInstance(processed['success'], int)
        self.assertIsInstance(processed['fail'], int)
        self.assertIsInstance(processed['running'], int)
        self.assertIsInstance(processed['queued'], int)


if __name__ == "__main__":
    # Run the tests and output results to a text file
    with open("TestResults.txt", "w") as f:
        f.write("Test Results:\n\n")
        runner = unittest.TextTestRunner(f, verbosity=2)
        unittest.main(testRunner=runner)
