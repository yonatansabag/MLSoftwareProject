from flask import Blueprint, render_template, request, jsonify, make_response, current_app, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import google.generativeai as genai
from google.generativeai.types import ContentType
from PIL import Image
import time
import random
from app import app, celery

# Create a Flask Blueprint named 'views'
views = Blueprint('views', __name__)

# Set your Google API key for generative AI
GOOGLE_API_KEY = "AIzaSyBb4ac6RgyxuARwEyfJs9VkjTRp_wiYjoM"
# Configure generative AI with the API key
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')


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

@celery.task
def describe_image(image_path):
    """
    Generates a textual description of an image using generative AI.

    Args:
        image_path (str): Path to the image file.

    Returns:
        str: Generated description of the image.
    """
    # TODO: Check if path is fined or need to send image
    text_prompt = "Describe the image"
    image = Image.open(image_path)
    prompt = [text_prompt, image]
    response = model.generate_content(prompt)
    if not response.text:
        self.update_state(state='FAILURE', meta={'error': 'Failed to generate description'})
        return {'error': 'Failed to generate description'}
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
            content_type = file.content_type

            if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in allowed_extensions \
                    or content_type not in ['image/png', 'image/jpeg', 'image/jpg']:
                current_app.config['FAILURE'] += 1
                return make_response(jsonify({'error': {'code': 400, 'message': 'Image is not PNG, JPG, or JPEG'}}),
                                     400)

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
    # TODO: Modify data to follow processes of upload image async
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

@app.route('/async_upload', methods=['POST'])
def async_upload_image():
    if 'image' not in request.files:
        return make_response(jsonify({'error': {'code': 400, 'message': 'No file part'}}), 400)

    file = request.files['image']
    if file.filename == '':
        return make_response(jsonify({'error': {'code': 400, 'message': 'No selected file'}}), 400)

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join('uploads', filename)
        file.save(file_path)
        allowed_extensions = ['png', 'jpg', 'jpeg']
        content_type = file.content_type

        if '.' not in filename or filename.rsplit('.', 1)[1].lower() not in allowed_extensions or content_type not in [
            'image/png', 'image/jpeg']:
            return make_response(jsonify({'error': {'code': 400, 'message': 'Image is not PNG or JPEG'}}), 400)

        # Send image to the classification API
        response = requests.post(
            'http://api_server:8000/classify',  # API endpoint
            files={'image': image}  # Send the image as file
        )

        if response.status_code == 200:
            result = response.json()
            return render_template('result.html', result=result)
        else:
            return 'Classification failed', 500




@app.route('/result/<req_id>', methods=['GET'])
def get_result(req_id):
    # Send image to the classification API
    response = requests.post(
        'http://api_server:8000/get_res',
        files={'req_id': req_id}
    )
    return jsonify(response)

    # if response.status_code == 200:
    #     result = response.json()
    #     return render_template('result.html', result=result)
    # else:
    #     return 'Classification failed', 500



@views.route('/game', methods=['GET'])
@login_required
def game():
    """
    Route to serve the game page.

    Returns:
        Template: 'game.html'
    """
    return render_template('game.html')


@views.route('/start_game', methods=['POST'])
def start_game():
    """
    Route to start a new game. It generates a hidden word and stores it in the session.

    Returns:
        JSON Response: Confirmation of game start.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    # model = genai.GenerativeModel('gemini-pro')
    generation_config = genai.GenerationConfig(
        stop_sequences=None,
        temperature=0.4,
        top_p=1.0,
        top_k=32,
        candidate_count=1,
        max_output_tokens=32,
    )

    prompt = """Generate a single, random word that is suitable for a word guessing game. The word should be neither 
    too common nor too obscure. Avoid generating repetitive words. The word should be easy 
    enough to guess but still provide a really small challenge. The output should be just one word, without any additional 
    characters, line breaks, or formatting."""

    hidden_word = model.generate_content(
        contents=prompt,
        generation_config=generation_config,
        stream=False,
    ).text

    # hidden_word = model.generate_content(prompt, temper).text
    # hidden_word = model.generate_content("""Generate a random word. This word will be used as the hidden word for a
    # word guessing game where players have to guess the word, So, generate a word that is easy to guess but not too
    # easy. You must return a SINGLE word as the output without any signs of new line, or ** or anything,
    # just a word. Be creative though, don't think only of 2 words and generate them repeatedly.""").text
    session['hidden_word'] = hidden_word
    session['game_over'] = False
    return jsonify({"message": "Game started! Make your guess."})


@views.route('/guess', methods=['POST'])
def guess():
    """
    Route to process a user's guess. It compares the guess to the hidden word.

    Returns:
        JSON Response: Distance between the guessed word and the hidden word.
    """
    if 'hidden_word' not in session or session['game_over']:
        return make_response(jsonify({'error': {'code': 400, 'message': 'Game not started or already over'}}), 400)

    user_guess = request.json.get('guess', '')
    if not user_guess:
        return make_response(jsonify({'error': {'code': 400, 'message': 'No guess provided'}}), 400)

    hidden_word = session['hidden_word']
    hidden_word = hidden_word.replace('\n', '').strip()

    # Use the Google Gemini API to compute the similarity
    # model = genai.GenerativeModel('gemini-1.5-flash')
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content([
        f"""How close is the word '{user_guess}' to '{hidden_word}'? Please provide a similarity score. You must 
        return a number between 1 to 10 where 1 means the words are very different and 10 means the words are very 
        similar. THE RETURN OUTPUT MUST BE A NUMBER. For example : the word "apple" and the word flower are somewhat 
        similar in the sense that they are both kind of plants. So the similarity score can be above 5 Another 
        example will be "Bike" and "Car" are similar in the sense that they are both vehicles. So, the similarity 
        score will be above 8. Another example is "Rain" and "Sunshine", they are not so far semantically. So, 
        the similarity score will be above 6. Last example will be "Dog" and "kitchen" are not similar at all. So, 
        the similarity score will be below 3. Please be creative and provide a similarity score based on your own 
        understanding. Do not classify all words as similar or dissimilar. Provide a score based on the context of 
        the words. if the words are the same, so the score is 10.""",
    ])

    try:
        score = float(response.text.strip())
    except ValueError:
        # If conversion fails, provide a default score or handle the error
        score = 0.0
        error_message = ("Could not convert the similarity score to a number. "
                         "Please try a different guess or contact support.")

        return jsonify({'message': error_message, 'score': score})

    # Optionally, check if the guess is correct
    if str(user_guess).strip().lower() == str(hidden_word).strip().lower():
        print("words are the same")
        session['game_over'] = True
        return jsonify({'message': 'Congratulations! You guessed the word!', 'score': score})

    return jsonify({'message': 'Keep trying!', 'score': score})


@views.route('/end_game', methods=['GET'])
def end_game():
    """
    Route to end the current game and clear the session.

    Returns:
        JSON Response: Confirmation of game end and hidden word.
    """
    hidden_word = session.pop('hidden_word', None)
    if hidden_word:
        hidden_word = hidden_word.replace('\n', '').strip()
    session['game_over'] = True
    return jsonify({'message': 'Game ended.', 'hidden_word': hidden_word})
