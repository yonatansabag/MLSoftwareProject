import threading
import time
from flask import Flask, request, jsonify, make_response, current_app
from pymongo import MongoClient
import random
from PIL import Image
import google.generativeai
import traceback
import io
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
# Set your Google API key for generative AI
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
# Configure generative AI with the API key
google.generativeai.configure(api_key=GOOGLE_API_KEY)
model = google.generativeai.GenerativeModel('gemini-1.5-flash')

# MongoDB setup
MONGO_URI = 'mongodb://mongo:27017/'  # if from machine
# MONGO_URI ='mongodb://localhost:27017/' #if local
client = MongoClient(MONGO_URI)
db = client['image_classification_db']
results_collection = db['results']


def create_app():
    """
    Creates and configures the Flask application.

    Returns:
        Flask: Configured Flask application instance.
    """
    app.config['START_TIME'] = time.time()
    app.config['SUCCESS'] = 0
    app.config['FAILURE'] = 0
    app.config['RUNNING'] = 0

    def process_image_in_background(app, image_data, request_id):
        """
        Process the image in the background and update the result in the database.
        """
        with app.app_context():  # Push the app context
            try:
                result = describe_image(image_data)
                results_collection.update_one(
                    {"request_id": request_id},
                    {"$set": {"result": result, "status": "completed"}}
                )
                current_app.config['SUCCESS'] += 1  # This will now work with app context
            except Exception as e:
                error_msg = f"Error processing image: {str(e)}\n{traceback.format_exc()}"
                print(error_msg)  # Log the error for debugging
                results_collection.update_one(
                    {"request_id": request_id},
                    {"$set": {"error": {'code': '500', 'message': error_msg}, "status": "error"}}
                )

    def describe_image(image_data):
        """
        Generates a textual description of an image using generative AI.

        Args:
            image_data: ...
            image_path (str): Path to the image file.

        Returns:
            str: Generated description of the image.
        """
        # TODO: Check if path is fined or need to send image
        try:
            text_prompt = "Describe the image"
            image = Image.open(io.BytesIO(image_data))
            prompt = [text_prompt, image]
            response = model.generate_content(prompt)
            result = [{"name": response.text, "score": '0.885'}]
            return result
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            return {'error': "Failed to describe image"}

    @app.route('/upload_image', methods=['POST'])
    def upload_image_sync():
        """
        Route for uploading an image and getting a synchronous response.
        Returns: JSON response with the image description.

        """
        if 'image' not in request.files:
            current_app.config['FAILURE'] += 1
            return make_response(jsonify({'error': {'code': 400, 'message': 'Api did not receive image'}}), 400)

        file = request.files['image']
        if file.filename == '':
            current_app.config['FAILURE'] += 1
            return make_response(jsonify({'error': {'code': 400, 'message': 'No selected file'}}), 400)

        if file and file.filename.rsplit('.', 1)[1].lower() not in ['jpg', 'jpeg', 'png']:
            current_app.config['FAILURE'] += 1
            return make_response(jsonify({'error': {'code': 400, 'message': 'Invalid file type'}}), 400)

        file_contents = file.read()
        if len(file_contents) == 0:
            current_app.config['FAILURE'] += 1
            return make_response(jsonify({'error': {'code': 400, 'message': 'Empty file'}}), 400)

        file.seek(0)
        try:
            image_data = file.read()
            description = describe_image(image_data)
            if isinstance(description, dict) and 'error' in description:
                current_app.config['FAILURE'] += 1
                return make_response(jsonify({'error': {'code': 500, 'message': description['error']}}), 500)
            else:
                current_app.config['SUCCESS'] += 1
                return make_response(jsonify({'matches': description}), 200)
        except Exception as e:
            error_message = f'Failed to process file: {str(e)}'

            return make_response(jsonify({'error': {'code': 500, 'message': error_message}}), 500)

    @app.route('/async_upload', methods=['POST'])
    def upload_image_async():
        """
        Route for uploading an image and getting an asynchronous response.
        Returns: JSON response with the request ID.

        """
        if 'image' not in request.files:
            current_app.config['FAILURE'] += 1
            return make_response(jsonify({'error': {'code': 400, 'message': 'Api did not receive image'}}), 400)

        file = request.files['image']
        if file.filename == '':
            current_app.config['FAILURE'] += 1
            return make_response(jsonify({'error': {'code': 400, 'message': 'No selected file'}}), 400)

        if file and file.filename.rsplit('.', 1)[1].lower() not in ['jpg', 'jpeg', 'png']:
            current_app.config['FAILURE'] += 1
            return make_response(jsonify({'error': {'code': 400, 'message': 'Invalid file type'}}), 400)

        file_contents = file.read()
        if len(file_contents) == 0:
            current_app.config['FAILURE'] += 1
            return make_response(jsonify({'error': {'code': 400, 'message': 'Empty file'}}), 400)

        file.seek(0)

        try:
            image_data = file.read()
            request_id = str(random.randint(10000, 1000000))
            results_collection.insert_one({"request_id": request_id, "result": [], "status": "running"})
            threading.Thread(target=process_image_in_background, args=(current_app._get_current_object(), image_data, request_id)).start()
            # sleep(3)

            return make_response(jsonify({'request_id': request_id}), 202)
        except Exception as e:

            error_message = f'Failed to process file: {str(e)}\n{traceback.format_exc()}'
            return make_response(jsonify({'error': {'code': 500, 'message': error_message}}), 500)

    @app.route('/result/<req_id>', methods=['GET'])
    def get_result(req_id):
        """
        Route for fetching the result of a specific request.
        Args:
            req_id: The request ID.

        Returns: JSON response with the status of the request and the matches if available.

        """
        result = retrieve_result(req_id)
        if result:
            status = result.get('status')
            if status == 'running':
                current_app.config['RUNNING'] += 1
                response = {
                    'status': status
                }
            elif status == 'completed':
                if current_app.config['RUNNING'] > 0:
                    current_app.config['RUNNING'] -= 1
                response = {
                    'status': status,
                    'matches': result.get('matches', [])
                }
            else:
                response = {
                    'status': status,
                    'error': result.get('error', {})
                }
            return make_response(jsonify(response), 200)
        else:
            error_response = {
                'status': 'error',
                'error': {
                    'code': 404,
                    'message': 'ID not found'
                }
            }
            return make_response(jsonify(error_response), 404)

    @app.route('/status', methods=['GET'])
    def status():
        """
        Route for fetching application status.

        Returns:
            JSON Response: Application uptime, success and failure counts, health status, and API version.
        """
        current_app.config['SUCCESS'] += 1
        data = {'status':
            {
                'uptime': time.time() - current_app.config['START_TIME'],
                'processed': {
                    'success': current_app.config['SUCCESS'],
                    'fail': current_app.config['FAILURE'],
                    'running': current_app.config['RUNNING'],
                    'queued': 0,
                }
            },
            'health': 'ok',
            'api_version': 0.23,
        }
        return make_response(jsonify(data), 200)

    return app


def retrieve_result(req_id):
    """
    Retrieve the result from MongoDB based on the request ID.

    Args:
        req_id (str): The request ID.

    Returns:
        dict: The result document from MongoDB, or None if not found.
    """
    # Retrieve result from MongoDB
    classification = results_collection.find_one({"request_id": req_id})
    if classification:
        # if matches is not in classification, return empty list

        matches = classification['result']
        return {
            'status': classification.get('status', 'unknown'),
            'matches': matches  # .get('result', [])
        }
    else:
        return None


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=6000, debug=True)
