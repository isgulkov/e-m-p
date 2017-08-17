import logging
from datetime import datetime, timedelta

from flask import Flask, render_template, redirect, request

from sqlalchemy import desc

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
    emails = Email.query.order_by(desc(Email.last_update)).all()

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

        enqueue_send_email(new_job.id)

        return redirect('/', code=302)

    return render_template('new_job.html', form=form)


def enqueue_send_email(job_id):
    job = EmailJob.query.filter(EmailJob.id == job_id).one()

    new_email = Email(
        job_id=job_id,
        dest_address=job.dest_address,
        subject=job.message_subject,
        content=job.message_content
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
    email = Email.query.filter(Email.uid == email_uid).one_or_none()

    if email is not None:
        email.job.status = 'COMPLETED'

        Email.query.filter(Email.job_id == email.job_id).delete()

        db_session.commit()

    return "", 204


@app.route('/_handle_send', methods=('POST', ))
def handle_send():
    if request.remote_addr != '0.1.0.2':  # IP from which GAE queue messages are sent
        return "", 403

    # Send the actual email

    email = Email.query.filter(Email.id == request.form['email_id']).one()

    message = EmailMessage(
        sender=config.SENDER_ADDRESS,
        subject=email.subject
    )

    message.to = email.dest_address
    message.body = email.content  # TODO: add notify <img> to body

    message.send()

    # Update the status of the Email in db

    email.status = 'SENT'
    email.last_update = datetime.now()

    db_session.commit()

    return "", 204


@app.route('/_cron_resend', methods=('GET', ))
def cron_resend():
    if request.remote_addr != '0.1.0.1':  # IP from which GAE cron requests are sent
        return "", 403

    RESEND_THRESHOLD = timedelta(seconds=5)  # TODO: move somewhere outwards

    # TODO: rewrite as one ORM query  vvvvvvvvvv

    uncompleted_jobs = EmailJob.query.join(Email).filter(
        EmailJob.status != 'COMPLETED'
    ).all()

    jobs_to_resend = []

    for job in uncompleted_jobs:
        if not any(email.last_update >= datetime.now() - RESEND_THRESHOLD for email in job.emails):
            jobs_to_resend.append(job)

    # TODO: rewrite as one ORM query  ^^^^^^^^^^

    for job_id in (job.id for job in jobs_to_resend):
        enqueue_send_email(job_id)

    return "", 204


@app.errorhandler(500)
def server_error(e):
    logging.exception("An error occurred during a request: %s" % e)
    return "An internal error occurred.", 500
