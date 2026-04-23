""" 
============================================================
Author:         Zachary Kao
Date Created:   2026-04-15
Description:    Core module for the Clinical Batch Trial Simulator.
                Creates the Flask app and registers API routes.
============================================================ 
"""

from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO

socketio = SocketIO()

def create_app():

    app = Flask(__name__)

    CORS(app)

    socketio.init_app(app, cors_allowed_origins="*")

    from core.src.api.routes import api_bp
    app.register_blueprint(api_bp)

    return app