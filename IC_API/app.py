####### SYNCHRONOUS VERSION #######
from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
import random
from PIL import Image
import google.generativeai as genai
import traceback
import io
import ast

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
# Set your Google API key for generative AI
GOOGLE_API_KEY = "AIzaSyBb4ac6RgyxuARwEyfJs9VkjTRp_wiYjoM"
# Configure generative AI with the API key
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# MongoDB setup
MONGO_URI = 'mongodb://localhost:27017/'  # Use the service name 'mongo' as defined in Docker Compose
# MONGO_URI ='mongodb://mongo:27017/'
client = MongoClient(MONGO_URI)
db = client['image_classification_db']  
results_collection = db['results']


def create_app():
    """
    Creates and configures the Flask application.

    Returns:
        Flask: Configured Flask application instance.
    """

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
            result = {"result": response.text}
            return result
        except Exception as e:
            return {'error': str(e)}

    # Endpoint for classifying an image
    @app.route('/classify', methods=['POST'])
    def classify_image():
        if 'image' not in request.files:
            return make_response(jsonify({'error': {'code': 400, 'message': 'Api did not receive image'}}), 400)

        file = request.files['image']

        if file.filename == '':
            return make_response(jsonify({'error': {'code': 400, 'message': 'No selected file'}}), 400)

        if file and file.filename.rsplit('.', 1)[1].lower() not in ['jpg', 'jpeg', 'png']:
            return make_response(jsonify({'error': {'code': 400, 'message': 'Invalid file type'}}), 400)
        try:
            image_data = file.read()
            request_id = str(random.randint(10000, 1000000))
            result = describe_image(image_data)
            results_collection.insert_one({
                "request_id": request_id,
                "matches": result,
                "status": "completed"  # Add a status field
            })
            return make_response(jsonify({'request_id': request_id}), 202)
        except Exception as e:
            error_message = f'Failed to process file: {str(e)}\n{traceback.format_exc()}'
            return make_response(jsonify({'error': {'code': 500, 'message': error_message}}), 500)

    @app.route('/result/<req_id>', methods=['GET'])
    def get_result(req_id):
        id = ast.literal_eval(req_id)['request_id']
        if not (id.isdigit() and 10000 <= int(id) <= 1000000):
            print('oof')
            error_response = {
                'error': {
                    'code': 400,
                    'message': 'Invalid request ID'
                }
            }
            return make_response(jsonify(error_response), 400)

        result = retrieve_result(id)
        
        if result:
            print('here')
            response = {
                'request_id': id,
                'status': result.get('status', 'unknown'),
                'result': result.get('matches', [])
            }
            return make_response(jsonify(response), 202)
        else:
            error_response = {
                'error': {
                    'code': 404,
                    'message': 'Result not found'
                }
            }
            return make_response(jsonify(error_response), 404)
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
    matches = classification['matches']
    if classification:
        return {
            'status': classification.get('status', 'unknown'),
            'matches': matches.get('result', [])
        }
    else:
        return None


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)



####### ASYNCHRONOUS VERSION #######
# from flask import Flask, request, jsonify, make_response
# from pymongo import MongoClient
# import random
# from PIL import Image
# import google.generativeai as genai
# import traceback
# import io
# import threading
#
# app = Flask(__name__)
# UPLOAD_FOLDER = 'uploads'
#
# # Set your Google API key for generative AI
# GOOGLE_API_KEY = "AIzaSyBb4ac6RgyxuARwEyfJs9VkjTRp_wiYjoM"
# # Configure generative AI with the API key
# genai.configure(api_key=GOOGLE_API_KEY)
# model = genai.GenerativeModel('gemini-1.5-flash')
#
# # MongoDB setup
# MONGO_URI = 'mongodb://mongo:27017/'  # Use the service name 'mongo' as defined in Docker Compose
# client = MongoClient(MONGO_URI)
# db = client['image_classification_db']  # Replace with your database name
# results_collection = db['results']  # Replace with your collection name
#
# def create_app():
#     app.config['SUCCESS'] = 0  # Counter for successful operations
#     app.config['FAILURE'] = 0  # Counter for failed operations
#
#     def describe_image(image_data):
#         try:
#             text_prompt = "Describe the image"
#             image = Image.open(io.BytesIO(image_data))
#             prompt = [text_prompt, image]
#             response = model.generate_content(prompt)
#             return {"result": response.text}
#         except Exception as e:
#             return {'error': str(e)}
#
#     def process_image_in_background(image_data, request_id):
#         try:
#             result = describe_image(image_data)
#             results_collection.update_one(
#                 {"request_id": request_id},
#                 {"$set": {"status": "COMPLETED", "result": result}}
#             )
#         except Exception as e:
#             results_collection.update_one(
#                 {"request_id": request_id},
#                 {"$set": {"status": "FAILED", "error": str(e)}}
#             )
#
#     @app.route('/classify', methods=['POST'])
#     def classify_image():
#         if 'image' not in request.files:
#             return make_response(jsonify({'error': {'code': 400, 'message': 'Api did not receive image'}}), 400)
#
#         file = request.files['image']
#         if file.filename == '':
#             return make_response(jsonify({'error': {'code': 400, 'message': 'No selected file'}}), 400)
#
#         if file and file.filename.rsplit('.', 1)[1].lower() not in ['jpg', 'jpeg', 'png']:
#             return make_response(jsonify({'error': {'code': 400, 'message': 'Invalid file type'}}), 400)
#
#         try:
#             image_data = file.read()
#             request_id = str(random.randint(10000, 1000000))
#             results_collection.insert_one({"request_id": request_id, "status": "PENDING"})
#             threading.Thread(target=process_image_in_background, args=(image_data, request_id)).start()
#             return make_response(jsonify({'request_id': request_id}), 202)
#         except Exception as e:
#             error_message = f'Failed to process file: {str(e)}\n{traceback.format_exc()}'
#             return make_response(jsonify({'error': {'code': 500, 'message': error_message}}), 500)
#
#     @app.route('/result/<req_id>', methods=['GET'])
#     def get_result(req_id):
#         if not (req_id.isdigit() and 10000 <= int(req_id) <= 1000000):
#             error_response = {
#                 'error': {
#                     'code': 400,
#                     'message': 'Invalid request ID'
#                 }
#             }
#             return make_response(jsonify(error_response), 400)
#
#         result = retrieve_result(req_id)
#         if result:
#             response = {
#                 'request_id': req_id,
#                 'status': result['status'],
#                 'result': result.get('result', [])
#             }
#             return jsonify(response), 200
#         else:
#             error_response = {
#                 'error': {
#                     'code': 404,
#                     'message': 'Result not found'
#                 }
#             }
#             return make_response(jsonify(error_response), 404)
#
#     return app
#
# def retrieve_result(req_id):
#     """
#     Retrieve the result from MongoDB based on the request ID.
#
#     Args:
#         req_id (str): The request ID.
#
#     Returns:
#         dict: The result document from MongoDB, or None if not found.
#     """
#     # Retrieve result from MongoDB
#     result = results_collection.find_one({"request_id": req_id})
#     if result:
#         return {
#             'status': result['status'],
#             'result': result.get('result', [])
#         }
#     else:
#         return None
#
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
