import logging

from flask import Flask, render_template, redirect

import config
from forms import NewTaskForm
from models import EmailTask
from database import db_session


app = Flask(__name__, template_folder='templates')


app.debug = config.DEBUG
app.secret_key = config.SECRET_KEY


@app.route('/')
def hello():
    result = ""

    for task in EmailTask.query.all():
        result += repr(task) + "<br/>"

    return result


@app.route('/new_task', methods=['GET', 'POST'])
def new_task():
    form = NewTaskForm()

    if form.validate_on_submit():
        new_task = EmailTask(
            dest_address=form.dest_address.data,
            message_subject=form.message_subject.data,
            message_content=form.message_content.data
        )

        db_session.add(new_task)
        db_session.commit()

        return redirect('/new_task', code=302)

    return render_template('new_task.html', form=form)


@app.errorhandler(500)
def server_error(e):
    logging.exception("An error occurred during a request: %s" % e)
    return "An internal error occurred.", 500
