import os
import sys
import time
import unittest
import requests
import numpy as np
from concurrent.futures import ThreadPoolExecutor, wait

MAX_RESPONSE_TIME_FACTOR = 1.1


class ImageUploadAPIStressTest(unittest.TestCase):
    """
    Stress test suite for the Image Upload API.
    Tests login, upload, and classification endpoints under various conditions.
    """

    def setUp(self):
        """Initialize test parameters and perform login."""
        self.api_url = 'http://127.0.0.1:8000/'
        self.test_image = "uploads/mamix.jpeg"
        self.credentials = {"username": "admin", "password": "admin"}
        self.timings = []

        login_resp = self.send_login_request()
        self.assertEqual(200, login_resp.status_code)
        self.session_cookies = login_resp.cookies

    def send_login_request(self):
        """Send a login request and return the response."""
        return requests.post(f"{self.api_url}login", data=self.credentials, allow_redirects=False)

    def verify_json_response(self, resp):
        """Check if the response is in JSON format."""
        self.assertEqual("application/json", resp.headers.get("Content-Type"))

    def upload_and_classify(self):
        """Upload an image and request classification."""
        with open(self.test_image, 'rb') as img:
            return requests.post(
                f"{self.api_url}classify_image",
                files={"image": img},
                data={'mode': 'sync'},
                cookies=self.session_cookies
            )

    def measure_classification_time(self):
        """Measure and store the time taken for image classification."""
        with open(self.test_image, 'rb') as img:
            for _ in range(6):
                start = time.time()
                resp = self.upload_and_classify()
                self.timings.append(time.time() - start)

                self.verify_json_response(resp)
                self.assertIn("matches", resp.json())
                self.assertEqual(200, resp.status_code)
                img.seek(0)

        self.avg_time = np.mean(self.timings)

    def test_concurrent_uploads(self):
        """Test the API's performance under concurrent upload stress."""
        self.measure_classification_time()

        new_session = self.send_login_request()
        self.assertEqual(200, new_session.status_code)

        start = time.time()
        with ThreadPoolExecutor() as executor:
            tasks = [executor.submit(self.upload_and_classify) for _ in range(6)]
            wait(tasks)
        total_duration = time.time() - start

        print(f"Average single upload time: {self.avg_time:.2f} seconds")
        print(f"Concurrent uploads total time: {total_duration:.2f} seconds")

        self.assertLess(
            total_duration,
            MAX_RESPONSE_TIME_FACTOR * self.avg_time,
            "Concurrent upload time exceeds acceptable limit."
        )


if __name__ == "__main__":
    unittest.main()