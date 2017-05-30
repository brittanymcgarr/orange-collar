import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_googlemaps import GoogleMaps
from config import base_directory

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
GoogleMaps(app)

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

from app import views, models