#!flask/bin/python
import os
from app import app

if __name__ == '__main__':
    app.debug = True
    
    if os.getenv('HEROKU') == '1':
        host = 'http://orange-collar.herokuapp.com'
    else:
        host = '0.0.0.0'
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host=host, port=port)