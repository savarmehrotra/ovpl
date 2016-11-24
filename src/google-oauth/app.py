from flask import Flask
from api import *
import config

def create_app(config):
    # init our app
    app = Flask(__name__)
    app.secret_key = 'development'
    # register blueprints
    app.register_blueprint(api)
    return app


#+NAME: run_server
if __name__ == "__main__":
    app = create_app(config)
    app.run(debug=True, host='0.0.0.0', threaded=True)
