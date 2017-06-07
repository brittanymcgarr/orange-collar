import os

# Global base directory
base_directory = os.path.abspath(os.path.dirname(__file__))

# WTForms
WTF_CSRF_ENABLED = True
SECRET_KEY = str(os.getenv('WTF_SECRET'))

if os.environ.get('HEROKU') != '1':
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(base_directory, 'app.db')
else:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

SQLALCHEMY_MIGRATE_REPO = os.path.join(base_directory, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = False

STATIC_DIR = os.path.join(base_directory, 'app/static')
IMAGES_DIR = os.path.join(STATIC_DIR, 'images')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

GOOGLEMAPS_KEY = os.environ.get('GOOG_KEY')

FLASKS3_BUCKET_NAME = 'orange-collar'
AWS_SECRET_ACCESS_KEY = str(os.getenv('AWS_SECRET_ACCESS_KEY'))
AWS_ACCESS_KEY_ID = str(os.getenv('AWS_ACCESS_KEY_ID'))
