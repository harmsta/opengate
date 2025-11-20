from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
import os
from .database import db

def create_app():
    app = Flask(__name__)

    app.secret_key = 'fakesecretkey'  
    app.permanent_session_lifetime = timedelta(minutes=30)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    DB_FILE_PATH = os.path.join(app.root_path, 'app_data.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_FILE_PATH}'
    
    app.config['SPOTIFY_CLIENT_ID'] = os.environ.get("CLIENT_ID") 
    app.config['SPOTIFY_CLIENT_SECRET'] = os.environ.get("CLIENT_SECRET") 
    app.config['SPOTIFY_REDIRECT_URI'] = os.environ.get("SPOTIFY_REDIRECT_URI") 
    
    db.init_app(app)

    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    with app.app_context():
        from . import models 
        db.create_all()

    return app
