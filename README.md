# WordGuess & Image Classification

Welcome to **WordGuess & Image Classification**, a web application where entertainment meets technology. The app offers multiple exciting features:

- **Authentication**: Sign up, log in, and log out securely.
- **Image Classification**: Classify images using our AI-powered service, available in both synchronous and asynchronous modes.
- **Collaborative Word Guessing Game**: Challenge yourself or collaborate with friends to guess words generated by an AI. Get feedback on how close your guesses are!

---

### 🛠️ Installation Steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yonatansabag/MLSoftwareProject.git
    ```
   
2. **Create a .env file:** In the root directory of the project, create a .env file to store your API keys. The file should contain:
    ```bash
    GOOGLE_API_KEY=<your-google-api-key>
    COHERE_KEY=<your-cohere-api-key>
    ```
    
3. **Build and run the Docker containers:** Use the provided Docker Compose setup to run the app.
    ```bash
    sudo docker-compose -f docker-compose-mongo.yml up --build
    ```

4. **Access the app:** Once the setup is complete, the application will be accessible at:
   
   *Main app: http://<your-server-ip>:80
   
   For example, if your IP address is 40.76.35.49, the app will be available at: 40.76.35.49:80

6. **Shut down Docker when finished**: To stop the containers and remove the services, run:
    ```bash
    sudo docker-compose -f docker-compose-mongo.yml down
    ```

   
