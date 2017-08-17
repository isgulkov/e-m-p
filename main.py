import logging
from datetime import datetime, timedelta

import flask
from sqlalchemy import desc
from google.appengine.api import taskqueue, mail
from flask.ext.httpauth import HTTPBasicAuth

import config
from forms import NewJobForm
from models import EmailJob, Email
from database import db_session


app = flask.Flask(__name__, template_folder='templates')


auth = HTTPBasicAuth()  # Only useful over HTTPS


app.debug = config.DEBUG
app.secret_key = config.SECRET_KEY


@auth.get_password
def get_pwd(username):
    # TODO: implement actual auth

    if username == 'admin':
        return 'admin'

    return None


@app.route('/')
@auth.login_required
def index_jobs():
    jobs_scheduled = EmailJob.query.filter(EmailJob.status == 'SCHEDULED')
    jobs_in_progress = EmailJob.query.filter(EmailJob.status == 'IN_PROGRESS')
    jobs_failed = EmailJob.query.filter(EmailJob.status == 'FAILED')
    jobs_completed = EmailJob.query.filter(EmailJob.status == 'COMPLETED')

    return flask.render_template(
        'index.html',
        jobs_scheduled=jobs_scheduled,
        jobs_in_progress=jobs_in_progress,
        jobs_failed=jobs_failed,
        jobs_completed=jobs_completed
    )


@app.route('/emails')
@auth.login_required
def index_emails():
    emails = Email.query.order_by(desc(Email.last_update)).all()

    return flask.render_template(
        'index_emails.html',
        emails=emails
    )


@app.route('/new_job', methods=('GET', 'POST', ))
@auth.login_required
def new_task():
    form = NewJobForm()

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

        return flask.redirect('/', code=302)

    return flask.render_template('new_job.html', form=form)


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

    taskqueue.Task(
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
    if flask.request.remote_addr != '0.1.0.2':  # IP from which GAE queue messages are sent
        return "", 403

    # Send the actual email

    email = Email.query.filter(Email.id == flask.request.form['email_id']).one()

    message = mail.EmailMessage(
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


def get_resend_threshold():
    return timedelta(minutes=1)  # TODO: something


@app.route('/_cron_resend', methods=('GET', ))
def cron_resend():
    if flask.request.remote_addr != '0.1.0.1':  # IP from which GAE cron requests are sent
        return "", 403

    uncompleted_jobs = EmailJob.query.join(Email).filter(
        EmailJob.status != 'COMPLETED'
    ).all()

    jobs_to_resend = []

    for job in uncompleted_jobs:
        if not any(email.last_update >= datetime.now() - get_resend_threshold() for email in job.emails):
            jobs_to_resend.append(job)

    # TODO: rewrite as one ORM query?

    for job_id in (job.id for job in jobs_to_resend):
        enqueue_send_email(job_id)

    return "", 204


@app.errorhandler(500)
def server_error(e):
    logging.exception("An error occurred during a request: %s" % e)
    return "An internal error occurred.", 500
