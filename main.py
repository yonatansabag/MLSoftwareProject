from website.app import run_server

IP = "0.0.0.0"
WEB_PORT = 8000
app,socketio = run_server()

if __name__ == '__main__':
    socketio.run(app, debug=True, host=IP, port=WEB_PORT, use_reloader=False, allow_unsafe_werkzeug=True)