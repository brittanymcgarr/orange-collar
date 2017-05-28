import os

# Global base directory
base_directory = os.path.abspath(os.path.dirname(__file__))

# WTForms
# Note: Secret key should be set in Heroku variables when deploying
WTF_CSRF_ENABLED = True
SECRET_KEY = str(os.getenv('WTF_SECRET'))

if os.environ.get('HEROKU') != '1':
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(base_directory, 'app.db')
else:
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

SQLALCHEMY_MIGRATE_REPO = os.path.join(base_directory, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = False
