from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
from celery_config import make_celery
import os
import random
from PIL import Image
from celery import Celery
from werkzeug.utils import secure_filename
import google.generativeai as genai
import traceback


app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'

# Set your Google API key for generative AI
GOOGLE_API_KEY = "AIzaSyBb4ac6RgyxuARwEyfJs9VkjTRp_wiYjoM"
# Configure generative AI with the API key
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')


def create_app():
    """
    Creates and configures the Flask application.

    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__)
    app.config['SUCCESS'] = 0  # Counter for successful operations
    app.config['FAILURE'] = 0  # Counter for failed operations
    # app.config['START_TIME'] = time.time()  # Application start time
    app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
    app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
    celery = make_celery(app)


    @celery.task(bind=True)
    def describe_image(self,image_data):
        """
        Generates a textual description of an image using generative AI.

        Args:
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
            return jsonify({"result": response.text})
        except Exception as e:
            self.update_state(state='FAILURE', meta={'error': str(e)})
            return {'error': str(e)}
        #TODO:
        # Save result to the database if necessary
        #db.results.insert_one({"result": result})


    # Endpoint for classifying an image
    @app.route('/classify', methods=['POST'])
    def classify_image():
        if 'image' not in request.files:
            return make_response(jsonify({'error': {'code': 400, 'message': 'Api did not receive image'}}), 400)

        file = request.files['image']

        if file.filename == '':
            return make_response(jsonify({'error': {'code': 400, 'message': 'No selected file'}}), 400)

        if file:
            print(f'file is {file}')
            try :
                image_data = file.read()

                request_id = str(random.randint(10000, 1000000))
                # TODO: ensure request id is unique (?)
                task = describe_image.apply_async(args=[image_data], task_id=request_id)
                return make_response(jsonify({'request_id': request_id}), 202)
            except Exception as e:
                error_message = f'Failed to process file: {str(e)}\n{traceback.format_exc()}'
                print(error_message)
                return make_response(jsonify({'error': {'code': 500, 'message': error_message}}), 500)



    # Endpoint for checking task status or result
    @app.route('/get_res', methods=['POST'])
    def get_result():
        # TODO: Handle id not found
        req_id = request.json.get('req_id')
        task = describe_image.AsyncResult(req_id)
        # SHOULD running if in queue or being processed
        if task.state == 'PENDING':
            response = {
                'status': 'running'
            }
        elif task.state == 'SUCCESS':
            response = {
                'status': 'completed',
                'result': task.result.get('result')
            }
        else:
            response = {
                'status': 'error',
                'error': task.result.get('error', 'Unknown error')
            }
        return jsonify(response)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', debug=True)
