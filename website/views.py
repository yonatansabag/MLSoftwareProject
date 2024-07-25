from flask import Blueprint, render_template, request, flash, jsonify, make_response, send_from_directory, Flask, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import time
import google.generativeai as genai
from google.generativeai.types import ContentType
from PIL import Image
import time

# Create a Flask Blueprint named 'views'
views = Blueprint('views', __name__)

# Set your Google API key for generative AI
GOOGLE_API_KEY = "AIzaSyBb4ac6RgyxuARwEyfJs9VkjTRp_wiYjoM"
# Configure generative AI with the API key
genai.configure(api_key=GOOGLE_API_KEY)

@views.route('/', methods=['GET', 'POST'])
def home():
    """
    Route for the home page.

    GET: Renders 'home.html' template.
    POST: Increments 'SUCCESS' counter in current app configuration.

    Returns:
        Template: 'home.html'
    """
    current_app.config['SUCCESS'] += 1
    return render_template("home.html", user=current_user)

def describe_image(image_path):
    """
    Generates a textual description of an image using generative AI.

    Args:
        image_path (str): Path to the image file.

    Returns:
        str: Generated description of the image.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    text_prompt = "Describe the image"
    image = Image.open(image_path)
    prompt = [text_prompt, image]
    response = model.generate_content(prompt)
    return response.text

@views.route('/upload_image',  methods=['GET', 'POST'])
@login_required
def upload_image():
    """
    Route for uploading an image and generating its description.

    GET: Renders 'index.html' template for uploading images.
    POST:
        - Checks if an image file is present.
        - Saves the uploaded file to 'uploads' directory.
        - Validates file format (PNG, JPG, JPEG).
        - Calls 'describe_image()' to generate description.
        - Returns JSON response with generated description.

    Returns:
        Template: 'index.html' (GET)
        JSON Response: Description of the uploaded image (POST)
    """
    if request.method == 'POST':
        if 'image' not in request.files:
            current_app.config['FAILURE'] += 1
            return make_response(jsonify({'error': {'code': 400, 'message': 'No file part'}}), 400)

        file = request.files['image']
        if file.filename == '':
            current_app.config['FAILURE'] += 1
            return make_response(jsonify({'error': {'code': 400, 'message': 'No selected file'}}), 400)

        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join('uploads', filename)
            file.save(file_path)
            allowed_extensions = ['png', 'jpg', 'jpeg']

            if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                current_app.config['FAILURE'] += 1
                return make_response(jsonify({'error': {'code': 400, 'message': 'Image is not PNG, JPG, or JPEG'}}), 400)

            description = describe_image(file_path)
            description = description.split('. ')
            result_string = '.\n'.join(description)
            current_app.config['SUCCESS'] += 1
            return make_response(jsonify({'matches': [{'name': result_string, 'score': 0.5}]}), 200)
    return render_template('index.html')

@views.route('/status', methods=['GET'])
def status():
    """
    Route for fetching application status.

    Returns:
        JSON Response: Application uptime, success and failure counts, health status, and API version.
    """
    current_app.config['SUCCESS'] += 1
    data = {
        'uptime': time.time() - current_app.config['START_TIME'],
        'processed': {
            'success': current_app.config['SUCCESS'],
            'fail': current_app.config['FAILURE'],
            'running': 0,
            'queued': 0,
        },
        'health': 'ok',
        'api_version': 0.21,
    }
    return make_response(jsonify(data), 200)

@views.route('/result/<request_id>', methods=['GET'])
@login_required
def result(request_id):
    """
    Route for fetching results based on request ID.

    Args:
        request_id (str): ID of the request.

    Returns:
        JSON Response: Error message indicating ID not found (HTTP 404).
    """
    return make_response(jsonify({'error': {'code': 404, 'message': 'ID not found'}}), 404)



