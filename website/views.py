import requests
from flask import Blueprint, render_template, request, jsonify, make_response, current_app, session, url_for
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os
import google.generativeai as genai
from PIL import Image
import time
import random
from sentence_transformers import SentenceTransformer
import numpy as np
from mongo.mongo_users import WordDatabase, db_words, GuessesDatabase, guesses
import cohere
from flask import redirect
from flask_socketio import join_room, leave_room, send, SocketIO, emit
from string import ascii_uppercase
from .app import socketio
#import socketio from main.py



# from website.app import create_socketio


# Create a Flask Blueprint named 'views'
views = Blueprint('views', __name__)

# Set your Google API key for generative AI
GOOGLE_API_KEY = "AIzaSyBb4ac6RgyxuARwEyfJs9VkjTRp_wiYjoM"
# Configure generative AI with the API key
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
co = cohere.Client("asNorrF7zKKhnbbpYVB0VZIs1UHu4MnTV1O3gXXe")
# embedding_model = SentenceTransformer("nomic-ai/nomic-embed-text-v1", trust_remote_code=True)

rooms = {}  # TODO: move to DB ??


# current_app.config['SECRET_KEY'] = 'safasfsa'

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
    # TODO: Check if path is fined or need to send image
    text_prompt = "Describe the image"
    image = Image.open(image_path)
    prompt = [text_prompt, image]
    response = model.generate_content(prompt)
    if not response.text:
        # self.update_state(state='FAILURE', meta={'error': 'Failed to generate description'})
        return {'error': 'Failed to generate description'}
    return response.text


@views.route('/upload_image', methods=['GET', 'POST'])
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


@views.route('/async_upload', methods=['POST'])
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
            files={'image': file}  # Send the image as file
        )

        if response.status_code == 200:
            result = response.json()
            return render_template('result.html', result=result)
        else:
            return 'Classification failed', 500


@views.route('/result/<req_id>', methods=['GET'])
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


def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        if code not in rooms:
            print(f"Code is: {code}")
            break
    return code


@views.route('/roomjoin', methods=['POST', 'GET'])
@login_required
def roomjoin():
    """
    Route to find or create a game room.

    Returns:
        Template: 'room.html'
    """
    session.clear()
    if request.method == "POST":
        print("It's post method")
        name = request.form.get("name")
        code = request.form.get("code")
        join = 'join' in request.form
        create = 'create' in request.form

        # Validate that the user has entered a name
        # print(f"create is : {create} of type {type(create)}")
        if not name:
            return render_template('room.html', error="Please enter a name", code=code, name=name)

        # Check if the user wants to join an existing room
        if join and not code:
            return render_template('room.html', error="Please enter a room code", code=code, name=name)

        room = code

        # Check if the user wants to create a new room
        if create:
            print("hello, i'm under the water, please help me")
            room = generate_unique_code(4)
            rooms[room] = {"members": 1, "game_started": False}
            session["room"] = room
            session["name"] = name
            return redirect(url_for('views.game', room_code=room))
        if join:
            # Check if the room code exists when trying to join a room
            if code not in rooms:
                return render_template('room.html', error="Room does not exist", code=code, name=name)
            rooms[code]["members"] += 1
            session["room"] = code
            session["name"] = name
            return redirect(url_for('views.game', room_code=code))


        # # Store the room and name in session
        # session["room"] = room
        # session["name"] = name  # Store user data in session temporarily
        #
        # # Redirect to the game page after room creation or joining
        # return redirect(url_for('views.game', room_code=room))

    return render_template('room.html')


@views.route('/game', methods=['GET', 'POST'])
def game():
    room = session.get('room')
    if room is None or room not in rooms:
        return redirect(url_for('views.roomjoin'))
    return render_template('game.html', room=room)


def setup_socketio_handlers(socketio):
    @socketio.on("join")
    def on_join(data):
        room = data.get("room")
        name = session.get("name")
        if not room or not name:
            return
        if room not in rooms:
            rooms[room] = {"members": 0}

        join_room(room)
        rooms[room]["members"] += 1
        print(f'{name} joined room {room}')
        emit('update_users', {'num_users': rooms[room]["members"]}, room=room)
        send({"name": name, "message": "has enterd the room"}, to=room)

    @socketio.on("leave")
    def on_leave(data):
        room = data.get("room")
        name = session.get("name")
        leave_room(room)

        if room in rooms:
            rooms[room]['members'] -= 1
            if rooms[room]['members'] <= 0:
                del rooms[room]
            else:
                emit('update_users', {'num_users': rooms[room]["members"]}, room=room)

        send({"name": name, "message": "has left the room"}, to=room)
        print(f'{name} has left room {room}')

    @socketio.on('disconnect')
    def handle_disconnect():
        room = session.get("room")
        name = session.get("name")
        if room and name:
            leave_room(room)
            if room in rooms:
                rooms[room]['members'] -= 1
                if rooms[room]['members'] <= 0:
                    del rooms[room]
                else:
                    emit('update_users', {'num_users': rooms[room]["members"]}, room=room)
            send({"name": name, "message": "has left the room"}, to=room)
            print(f'{name} has left room {room}')




@views.route('/start_game', methods=['POST'])
def start_game():
    """
    Route to start a new game. It generates a hidden word and stores it in the session.

    Returns:
        JSON Response: Confirmation of game start.
    """
    room = session.get("room")

    if room is None or room not in rooms:
        return jsonify({"error": "Room not found"}), 400

    # Check if the game is already started
    if rooms[room].get('game_started', False):
        return jsonify({"message": "Game already started!", "hidden_word": rooms[room]['hidden_word']}), 200

    # Generate the hidden word
    model = genai.GenerativeModel('gemini-pro')
    generation_config = genai.GenerationConfig(
        stop_sequences=None,
        temperature=0.7,
        top_p=1.0,
        top_k=32,
        candidate_count=1,
        max_output_tokens=32,
    )

    prompt = """Generate a single, random word suitable for a word guessing game for people who are not native in English.
    The word should be common and should be easy to guess. 
    Ensure the word is distinct. Do not use words that have been generated recently. The output should be a single 
    word with no additional characters, spaces, line breaks, or formatting."""

    while True:
        # Generate a word
        hidden_word = model.generate_content(
            contents=prompt,
            generation_config=generation_config,
            stream=False,
        ).text.strip()

        # Check if the word already exists in the database
        if not WordDatabase.get(hidden_word.lower()):
            # If it doesn't exist, add it to the database
            WordDatabase.add_word(hidden_word.lower())
            print(f"Hidden word: {hidden_word}")
            break
        else:
            # If it exists, generate a new word
            continue

    # Update room state
    rooms[room]['hidden_word'] = hidden_word
    rooms[room]['game_started'] = True
    rooms[room]['game_over'] = False

    # Notify users that the game has started
    socketio.emit('game_started', {'game_started': True, 'hidden_word': hidden_word}, room=room)

    return jsonify({"message": "Game started! Make your guess."})


@views.route('/guess', methods=['POST'])
def guess():
    """
    Route to process a user's guess. It compares the guess to the hidden word.

    Returns:
        JSON Response: Distance between the guessed word and the hidden word.
    """
    room = session.get("room")
    if room is None or room not in rooms or rooms[room].get('game_over'):
        return make_response(jsonify({'error': {'code': 400, 'message': 'Game not started or already over'}}), 400)

    # if 'hidden_word' not in session or session['game_over']:
    #     return make_response(jsonify({'error': {'code': 400, 'message': 'Game not started or already over'}}), 400)

    hidden_word = rooms[room].get('hidden_word')
    user_guess = request.json.get('guess', '')
    GuessesDatabase.print_all()
    if not user_guess:
        return make_response(jsonify({'error': {'code': 400, 'message': 'No guess provided'}}), 400)

    def cosine_similarity(vec1, vec2):
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        norm_vec1 = np.linalg.norm(vec1)
        norm_vec2 = np.linalg.norm(vec2)
        cosine_sim = dot_product / (norm_vec1 * norm_vec2)
        return cosine_sim

    def similarity_score(vec1, vec2):
        # Get cosine similarity
        cosine_sim = cosine_similarity(vec1, vec2)
        # Adjust to a 0-1 scale
        score = (1 + cosine_sim) / 2
        return score

    hidden_word = hidden_word.replace('\n', '').strip()
    texts = [hidden_word, user_guess]
    embeddings = co.embed(texts=texts, input_type="search_document", model="embed-english-v3.0").embeddings
    # hidden_word_embeddings = embedding_model.encode(hidden_word)
    # user_guess_embeddings = embedding_model.encode(user_guess)

    try:
        # score = float(response.text.strip())
        print(f"Hidden word is : {hidden_word}")
        # score = similarity_score(hidden_word_embeddings, user_guess_embeddings)
        score = similarity_score(embeddings[0], embeddings[1])
        # round the score to be out of 10 and with only one number after the dot
        score = round(score * 10, 1)
        score = round(score * 2 - 10, 1)
        GuessesDatabase.add_word(user_guess, score)
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


@views.route('/all_words', methods=['GET'])
def all_words():
    words = GuessesDatabase.print_all()
    return jsonify(words)


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
    guesses.drop()
    return jsonify({'message': 'Game ended.', 'hidden_word': hidden_word})
