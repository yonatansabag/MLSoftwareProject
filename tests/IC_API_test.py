import unittest
import requests
import time
import os
from PIL import Image
import io


class TestImageClassificationAPI(unittest.TestCase):
    BASE_URL = 'http://127.0.0.1:5000'

    def setUp(self):
        # Create a test image
        self.test_image_path = 'test_image.jpg'
        self.create_test_image(self.test_image_path)

        # Create a test text file
        self.test_text_path = 'test.txt'
        with open(self.test_text_path, 'w') as f:
            f.write("This is a test text file.")

        # Create a large test image
        self.large_image_path = 'large_test_image.jpg'
        self.create_large_test_image(self.large_image_path)

    def tearDown(self):
        # Clean up created files
        for file_path in [self.test_image_path, self.test_text_path, self.large_image_path]:
            if os.path.exists(file_path):
                os.remove(file_path)

    def create_test_image(self, path, size=(100, 100), color='red'):
        img = Image.new('RGB', size, color=color)
        img.save(path)

    def create_large_test_image(self, path, size=(5000, 5000)):
        self.create_test_image(path, size=size, color='blue')

    def test_upload_sync_valid_image(self):
        url = f'{self.BASE_URL}/upload_sync'
        with open(self.test_image_path, 'rb') as img:
            files = {'image': ('test_image.jpg', img, 'image/jpeg')}
            response = requests.post(url, files=files)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('matches', data)
        self.assertIsInstance(data['matches'], list)
        self.assertTrue(len(data['matches']) > 0)

    def test_upload_sync_invalid_file(self):
        url = f'{self.BASE_URL}/upload_sync'
        with open(self.test_text_path, 'rb') as txt:
            files = {'image': ('test.txt', txt, 'text/plain')}
            response = requests.post(url, files=files)
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_upload_sync_no_file(self):
        url = f'{self.BASE_URL}/upload_sync'
        response = requests.post(url)
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_upload_async_valid_image(self):
        url = f'{self.BASE_URL}/upload_async'
        with open(self.test_image_path, 'rb') as img:
            files = {'image': ('test_image.jpg', img, 'image/jpeg')}
            response = requests.post(url, files=files)
        self.assertEqual(response.status_code, 202)
        data = response.json()
        self.assertIn('request_id', data)

    def test_upload_async_invalid_file(self):
        url = f'{self.BASE_URL}/upload_async'
        with open(self.test_text_path, 'rb') as txt:
            files = {'image': ('test.txt', txt, 'text/plain')}
            response = requests.post(url, files=files)
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_get_result_valid_id(self):
        upload_url = f'{self.BASE_URL}/upload_async'
        with open(self.test_image_path, 'rb') as img:
            files = {'image': ('test_image.jpg', img, 'image/jpeg')}
            upload_response = requests.post(upload_url, files=files)
        self.assertEqual(upload_response.status_code, 202)
        request_id = upload_response.json()['request_id']

        result_url = f'{self.BASE_URL}/result/{request_id}'
        max_retries = 10
        for _ in range(max_retries):
            response = requests.get(result_url)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            if data['status'] == 'completed':
                self.assertIn('matches', data)
                self.assertIsInstance(data['matches'], list)
                self.assertTrue(len(data['matches']) > 0)
                return
            time.sleep(1)

        self.fail("Result processing did not complete in time")

    def test_get_result_invalid_id(self):
        url = f'{self.BASE_URL}/result/invalid_id'
        response = requests.get(url)
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.json())

    # New tests

    def test_upload_sync_large_image(self):
        url = f'{self.BASE_URL}/upload_sync'
        with open(self.large_image_path, 'rb') as img:
            files = {'image': ('large_test_image.jpg', img, 'image/jpeg')}
            response = requests.post(url, files=files)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('matches', data)

    def test_upload_async_large_image(self):
        url = f'{self.BASE_URL}/upload_async'
        with open(self.large_image_path, 'rb') as img:
            files = {'image': ('large_test_image.jpg', img, 'image/jpeg')}
            response = requests.post(url, files=files)
        self.assertEqual(response.status_code, 202)
        self.assertIn('request_id', response.json())

    def test_upload_sync_empty_file(self):
        url = f'{self.BASE_URL}/upload_sync'
        files = {'image': ('empty.jpg', io.BytesIO(), 'image/jpeg')}
        response = requests.post(url, files=files)
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_upload_async_empty_file(self):
        url = f'{self.BASE_URL}/upload_async'
        files = {'image': ('empty.jpg', io.BytesIO(), 'image/jpeg')}
        response = requests.post(url, files=files)
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())

    def test_concurrent_uploads(self):
        url = f'{self.BASE_URL}/upload_async'
        request_ids = []
        num_concurrent = 5

        with open(self.test_image_path, 'rb') as img:
            file_content = img.read()

        for _ in range(num_concurrent):
            files = {'image': ('test_image.jpg', file_content, 'image/jpeg')}
            response = requests.post(url, files=files)
            self.assertEqual(response.status_code, 202)
            request_ids.append(response.json()['request_id'])

        for request_id in request_ids:
            result_url = f'{self.BASE_URL}/result/{request_id}'
            max_retries = 20
            for _ in range(max_retries):
                response = requests.get(result_url)
                self.assertEqual(response.status_code, 200)
                if response.json()['status'] == 'completed':
                    break
                time.sleep(1)
            else:
                self.fail(f"Result processing did not complete in time for request_id: {request_id}")

    def test_get_result_multiple_times(self):
        upload_url = f'{self.BASE_URL}/upload_async'
        with open(self.test_image_path, 'rb') as img:
            files = {'image': ('test_image.jpg', img, 'image/jpeg')}
            upload_response = requests.post(upload_url, files=files)
        self.assertEqual(upload_response.status_code, 202)
        request_id = upload_response.json()['request_id']

        result_url = f'{self.BASE_URL}/result/{request_id}'
        max_retries = 10
        for _ in range(max_retries):
            response = requests.get(result_url)
            self.assertEqual(response.status_code, 200)
            if response.json()['status'] == 'completed':
                break
            time.sleep(1)
        else:
            self.fail("Result processing did not complete in time")

        # Get the result multiple times
        for _ in range(3):
            response = requests.get(result_url)
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data['status'], 'completed')
            self.assertIn('matches', data)


if __name__ == '__main__':
    unittest.main()
