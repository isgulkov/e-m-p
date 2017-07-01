import logging

from flask import Flask

import config


app = Flask(__name__)


app.debug = config.DEBUG
app.secret_key = config.SECRET_KEY


@app.route('/')
def hello():
    return "TY PIDOR!"


@app.errorhandler(500)
def server_error(e):
    logging.exception("An error occurred during a request: %s" % e)
    return "An internal error occurred.", 500
