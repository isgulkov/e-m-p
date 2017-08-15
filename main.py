import logging

from flask import Flask, render_template, redirect, request

import config
from forms import NewTaskForm
from models import EmailJob
from database import db_session

from google.appengine.api.taskqueue import Queue, Task


app = Flask(__name__, template_folder='templates')


app.debug = config.DEBUG
app.secret_key = config.SECRET_KEY


@app.route('/')
def hello():
    jobs_scheduled = EmailJob.query.filter(EmailJob.status == 'SCHEDULED')
    jobs_in_progress = EmailJob.query.filter(EmailJob.status == 'IN_PROGRESS')
    jobs_failed = EmailJob.query.filter(EmailJob.status == 'FAILED')
    jobs_completed = EmailJob.query.filter(EmailJob.status == 'COMPLETED')

    return render_template(
        'index.html',
        jobs_scheduled=jobs_scheduled,
        jobs_in_progress=jobs_in_progress,
        jobs_failed=jobs_failed,
        jobs_completed=jobs_completed
    )


@app.route('/new_job', methods=('GET', 'POST', ))
def new_task():
    form = NewTaskForm()

    if form.validate_on_submit():
        dest_address = form.dest_address.data
        message_subject = form.message_subject.data
        message_content = form.message_content.data

        new_job = EmailJob(
            dest_address=dest_address,
            message_subject=message_subject,
            message_content=message_content
        )

        db_session.add(new_job)

        db_session.commit()

        enqueue_send_task(new_job.id, dest_address, message_subject, message_content)

        return redirect('/', code=302)

    return render_template('new_job.html', form=form)


def enqueue_send_task(job_id, dest_address, message_subject="", message_content=""):
    Task(
        url='/_handle_send',
        params={
            'job_id': job_id,
            'dest_address': dest_address,
            'message_subject': message_subject,
            'message_content': message_content
        }
    ).add(queue_name='queue-send')


@app.route('/_handle_send', methods=('POST', ))
def handle_send():
    print "typa poslali: %s" % request.data

    return ("", 204)


@app.route('/_cron_resend', methods=('GET', ))
def cron_resend():
    # TODO: find jobs for which there are no opened emails and resend

    pass


@app.route('/_handle_notify', methods=('POST', ))
def handle_nofify():
    # Handle open notification task

    pass


@app.errorhandler(500)
def server_error(e):
    logging.exception("An error occurred during a request: %s" % e)
    return "An internal error occurred.", 500
