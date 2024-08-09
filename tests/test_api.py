import unittest
import requests
import os
import concurrent.futures

class TestImageClassificationAPI(unittest.TestCase):

    def setUp(self):
        script_dir = os.path.dirname(__file__)
        self.valid_image_file = os.path.join(os.path.dirname(__file__), '..', 'uploads', 'flag.png')
        self.invalid_image_file = os.path.join(os.path.dirname(__file__), '..', 'uploads',
                                               'Yahav_Cohen_CV_.pdf')  # Non-image file
        self.non_existent_image_file = os.path.join(script_dir, '../uploads/non_existent.jpg')

    def test_classify_valid_image(self):
        url = "http://localhost:5000/classify"
        with open(self.valid_image_file, "rb") as image_file:
            files = {'image': image_file}
            response = requests.post(url, files=files)
            print(response)
        self.assertEqual(response.status_code, 202)
        requested_id = response.json()['request_id']
        url_result = f"http://localhost:5000/result/{requested_id}"
        response_result = requests.get(url_result)
        print(response_result.json())
        self.assertEqual(response_result.status_code, 200)

    # def classify_image(self):
    #     url = "http://localhost:5000/classify"
    #     with open(self.valid_image_file, "rb") as image_file:
    #         files = {'image': image_file}
    #         response = requests.post(url, files=files)
    #         return response
    #
    # def test_classify_valid_image_concurrent(self):
    #     # Number of concurrent requests to send
    #     num_requests = 20
    #
    #     # Use ThreadPoolExecutor to send multiple requests concurrently
    #     with concurrent.futures.ThreadPoolExecutor(max_workers=num_requests) as executor:
    #         futures = [executor.submit(self.classify_image) for _ in range(num_requests)]
    #         responses = [future.result() for future in concurrent.futures.as_completed(futures)]
    #
    #     for response in responses:
    #         self.assertEqual(response.status_code, 202)
    #         requested_id = response.json()['request_id']
    #         url_result = f"http://localhost:5000/result/{requested_id}"
    #         response_result = requests.get(url_result)
    #         print(response_result.json())
    #         self.assertEqual(response_result.status_code, 200)

    # def test_get_result_with_valid_id(self):
    #     # Assuming request_id '12345' exists; adjust based on actual test environment
    #     url = "http://localhost:5000/get_res"
    #     data = {'req_id': '12345'}
    #     response = requests.post(url, json=data)
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIn('status', response.json())

    # def test_get_result_with_invalid_id(self):
    #     url = "http://localhost:5000/get_res"
    #     data = {'req_id': 'invalid_id'}
    #     response = requests.post(url, json=data)
    #     self.assertEqual(response.status_code, 404)
    #     self.assertIn('error', response.json())

    # def test_get_result_without_id(self):
    #     url = "http://localhost:5000/get_res"
    #     response = requests.post(url, json={})
    #     self.assertEqual(response.status_code, 400)
    #     self.assertIn('error', response.json())


if __name__ == '__main__':
    unittest.main()