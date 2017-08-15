import logging

from flask import Flask, render_template, redirect

import config
from forms import NewTaskForm
from models import EmailTask
from database import db_session

from google.appengine.api import taskqueue


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


@app.route('/new_task', methods=('GET', 'POST', ))
def new_task():
    form = NewTaskForm()

    if form.validate_on_submit():
        dest_address = form.dest_address.data
        message_subject = form.message_subject.data
        message_content = form.message_content.data

        new_task = EmailTask(
            dest_address=dest_address,
            message_subject=message_subject,
            message_content=message_content
        )

        db_session.add(new_task)

        taskqueue.add(
            url='/_handle_send',
            params={
                'dest_adress': dest_address,
                'message_subject': message_subject,
                'message_content': message_content
            }
        )

        # The task is intentionally not saved to the db until and unless it is enqueued in the gcloud task queue

        db_session.commit()

        return redirect('/', code=302)

    return render_template('new_task.html', form=form)


@app.route('/_handle_send', methods=('POST', ))
def handle_send():
    # Handle task to send mail

    pass


@app.route('/_handle_notify', methods=('POST', ))
def handle_nofify():
    # Handle open notification task

    pass


@app.errorhandler(500)
def server_error(e):
    logging.exception("An error occurred during a request: %s" % e)
    return "An internal error occurred.", 500
