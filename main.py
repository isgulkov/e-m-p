import logging

from flask import Flask, render_template

import config
from forms import NewTaskForm


app = Flask(__name__, template_folder='templates')


app.debug = config.DEBUG
app.secret_key = config.SECRET_KEY


@app.route('/')
def hello():
    return "TY PIDOR!"


@app.route('/new_task', methods=['GET', 'POST'])
def new_task():
    form = NewTaskForm()

    if form.validate_on_submit():
        return "%s<br/>%s<br/>%s" % (form.dest_address.data, form.message_subject.data, form.message_text.data, )

    return render_template('new_task.html', form=form)


@app.errorhandler(500)
def server_error(e):
    logging.exception("An error occurred during a request: %s" % e)
    return "An internal error occurred.", 500
