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
    tasks_scheduled = EmailTask.query.filter(EmailTask.status=='SCHEDULED')
    tasks_in_progress = EmailTask.query.filter(EmailTask.status=='IN_PROGRESS')
    tasks_failed = EmailTask.query.filter(EmailTask.status=='FAILED')
    tasks_completed = EmailTask.query.filter(EmailTask.status=='COMPLETED')

    return render_template(
        'index.html',
        tasks_scheduled=tasks_scheduled,
        tasks_in_progress=tasks_in_progress,
        tasks_failed=tasks_failed,
        tasks_completed=tasks_completed
    )


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

        return redirect('/', code=302)

    return render_template('new_task.html', form=form)


@app.errorhandler(500)
def server_error(e):
    logging.exception("An error occurred during a request: %s" % e)
    return "An internal error occurred.", 500
