from website.app import run_server

app,socketio = run_server()

if __name__ == '__main__':
    # app.run(host='0.0.0.0', debug=True)

    socketio.run (app, debug = True)


