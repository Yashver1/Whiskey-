from flask import Flask
from flask import Response
flask_app = Flask(__name__)


@flask_app.route("/")
def hello():
    return Response(
        '<div>Welcome to Flask!</div>\n',
        mimetype='text/html'
    )


app = flask_app.wsgi_app
