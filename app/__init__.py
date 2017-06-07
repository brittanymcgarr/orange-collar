import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_googlemaps import GoogleMaps
from flask_s3 import FlaskS3

from config import base_directory, GOOGLEMAPS_KEY

app = Flask(__name__)
app.config.from_object('config')

s3 = FlaskS3()
s3.init_app(app)

db = SQLAlchemy(app)

GoogleMaps(app, key=GOOGLEMAPS_KEY)

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

from app import views, models