import os
import sys
import time
import unittest
import requests
import numpy as np
import concurrent.futures

FAST_REPLY_TIME_RATIO = 1.1


class StressTestImageUploadAPITest(unittest.TestCase):
    """
    Test suite for the Image Upload API.
    This suite tests various endpoints of an image upload service including login, upload, and user management.
    """
    def setUp(self):
        """
        Set up test variables and URLs.
        This method runs before each test case.
        """
        self.base_url = f'http://127.0.0.1:8000/'
        self.valid_image_file = "uploads/mamix.jpeg"
        self.login_data = {"username": "admin", "password": "admin"}
        self.T = []

        login_response = requests.post(self.base_url + "login", data=self.login_data, allow_redirects=False)
        self.assertEqual(302, login_response.status_code)
        self.login_response = login_response


    def _resp_is_json(self, response):
        """
        Helper method to check if response is JSON.
        :param response: Response object to check.
        """
        self.assertEqual("application/json", response.headers.get("Content-Type", ""))


    def classify_image(self):
        with open(self.valid_image_file, 'rb') as file:
            response = requests.post(
                                    self.base_url + "classify_image",
                                    files={"image": file},
                                    data={'method': 'sync'},
                                    cookies=self.login_response.cookies)
            return response


    def _test_average_time_to_classify(self):
        """
        Test Average time to upload and classify an image with valid login credentials.
        """
        with open(self.valid_image_file, 'rb') as file:
            for _ in range(6):
                start_time = time.time()
                response = self.classify_image()
                self.T.append(time.time() - start_time)

                self._resp_is_json(response)
                self.assertIn("matches", response.json())
                self.assertEqual(200, response.status_code)
                file.seek(0)

        self.T = np.array(self.T).mean()


    def test_stress_sync(self):
        """
        Test the system under stress by sending 6 parallel synchronous classification requests.
        """
        self._test_average_time_to_classify()

        login_response = requests.post(self.base_url + "login", data=self.login_data, allow_redirects=False)
        self.assertEqual(302, login_response.status_code)

        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(self.classify_image) for _ in range(6)]
            concurrent.futures.wait(futures)
        total_time = time.time() - start_time

        print(f"Average time for single image classification: {self.T} seconds")
        print(f"Total time for 6 concurrent requests: {total_time} seconds")
        self.assertLess(total_time, FAST_REPLY_TIME_RATIO * self.T, "Response time exceeds the expected ratio.")


if __name__ == "__main__":
    unittest.main()