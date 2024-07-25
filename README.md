# Flask Photo Uploader with Gemini Integration

## Overview

This Flask application allows users to sign up, log in, and upload photos. Each uploaded photo is analyzed by Gemini to provide descriptions. The application tracks all upload attempts and their statuses, providing a JSON-based status endpoint.

## Features

- **User Authentication**: Users can sign up and log in with secure password storage.
- **Photo Upload**: After logging in, users can upload photos.
- **Gemini Integration**: Automatically analyze and describe uploaded photos.
- **Status Tracking**: Monitor all photo uploads and their success or failure statuses.
- **JSON Responses**: Consistent JSON responses for API interactions.

## Installation

1. **Clone the repository**:
    ```sh
    git clone https://github.com/yonatansabag/MLSoftwareProject.git
    cd MLSoftwareProject.git
    ```

2. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

3. **Set up the database**:
    ```sh
    flask db init
    flask db migrate
    flask db upgrade
    ```
4. **Configure Google API Key**:
   In `app.py`, replace `Your API key` in the line:
   ```python
   GOOGLE_API_KEY = "Your API key"

5. **Run the application**:
    ```sh
    python main.py
    ```

## Endpoints

### User Authentication

- **Sign Up**: Allows new users to register by providing a username and password.
- **Log In**: Allows existing users to log in with their credentials.

### Photo Upload

- **Upload Photo**: Users can upload photos which will be analyzed by Gemini to provide a description.

### Status Tracking

- **Get Status**: Provides a list of all photo upload attempts and their statuses.

## Flash Messages

Flash messages are displayed to users for various actions like login success, enhancing user experience.

## Custom Login Required

The application includes a custom login required decorator to ensure only authenticated users can access certain routes.

## HTML Templates

The application uses HTML templates with integrated styles for uploading images and displaying results.

## Contributing

If you wish to contribute to this project, please create a fork of the repository, make your changes in a new branch, and submit a pull request.

## License

This project is licensed under the MIT License.

## Contact

For any queries, please contact yahav1349@gmail.com
