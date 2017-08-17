import logging
from datetime import datetime

from flask import Flask, render_template, redirect, request

import config
from forms import NewTaskForm
from models import EmailJob, Email
from database import db_session

from google.appengine.api.taskqueue import Task
from google.appengine.api.mail import EmailMessage


app = Flask(__name__, template_folder='templates')


app.debug = config.DEBUG
app.secret_key = config.SECRET_KEY


@app.route('/')
def index_jobs():
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


@app.route('/emails')
def index_emails():
    emails = Email.query.all()

    return render_template(
        'index_emails.html',
        emails=emails
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

        enqueue_send_email(new_job.id, dest_address, message_subject, message_content)

        return redirect('/', code=302)

    return render_template('new_job.html', form=form)


def enqueue_send_email(job_id, dest_address, message_subject="", message_content=""):
    new_email = Email(
        job_id=job_id,
        dest_address=dest_address,
        subject=message_subject,
        content=message_content
    )

    db_session.add(new_email)
    db_session.commit()

    Task(
        url='/_handle_send',
        params={
            'email_id': new_email.id
        }
    ).add(queue_name='queue-send')


@app.route('/notify/<email_uid>', methods=('GET', ))
def process_notify(email_uid):
    email = Email.query.filter(Email.uid==email_uid).one()

    email.status = 'OPENED'

    email.job.status = 'COMPLETED'

    db_session.commit()

    return "", 204


@app.route('/_handle_send', methods=('POST', ))
def handle_send():
    if request.remote_addr != '0.1.0.2':
        return "", 403

    # Send the actual email

    email = Email.query.filter(id==request.data['email_id']).one()

    message = EmailMessage(
        sender=config.SENDER_ADDRESS,
        subject=email.subject
    )

    message.to = email.dest_address
    message.body = email.content # TODO: add notify <img> to body

    message.send()

    # Update the status of the Email in db

    email.status = 'SENT'
    email.sent_date = datetime.now()

    db_session.commit()

    return "", 204


@app.route('/_cron_resend', methods=('GET', ))
def cron_resend():
    if request.remote_addr != '0.1.0.2':
        return "", 403

    # TODO: find uncompleted jobs for which there are emails send before threshold
    # TODO: enqueue resend and add corresponding email to db

    pass


@app.errorhandler(500)
def server_error(e):
    logging.exception("An error occurred during a request: %s" % e)
    return "An internal error occurred.", 500
