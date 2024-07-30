from flask import Flask, request, jsonify
from pymongo import MongoClient
from celery_config import make_celery

app = Flask(__name__)

# MongoDB client setup
client = MongoClient("mongodb://mongodb:27017/")
db = client["image_classification"]


def create_app():
    """
    Creates and configures the Flask application.

    Returns:
        Flask: Configured Flask application instance.
    """
    app = Flask(__name__)
    app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
    app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
    db.init_app(app)  # Initialize SQLAlchemy with the app instance
    celery = make_celery(app)

    from .views import views
    from .auth import auth

    # Register blueprints for different parts of the application
    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')


    return app

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
    return jsonify({"result": response.text})
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
        filename = secure_filename(file.filename)
        file_path = os.path.join('uploads', filename)
        file.save(file_path)

        request_id = random.randint(10000, 1000000)
        # TODO: ensure request id is unique (?)
        task = describe_image.apply_async(args=[file_path], task_id=str(request_id))
        return make_response(jsonify({'request_id': request_id}), 202)


# Endpoint for classifying an image
@app.route('/get_res', methods=['POST'])
def classify_image():
    # TODO: Handle id not found
    req_id = request.files['req_id']
    task = describe_image.AsyncResult(req_id)
    # SHOULD running if in queue or being processed
    if task.state == 'PENDING':
        response = {
            'status': 'running'
        }
    elif task.state != 'FAILURE':
        response = {
            'status': 'completed',
            # 'state': task.state,
            'matches': task.result
        }
    else:
        response = {
            'status': 'error',
            'error': task.result  # might be task.state
        }
    return  response



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
