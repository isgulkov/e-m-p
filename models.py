from random import choice
from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, Text, Enum, DateTime
from sqlalchemy.orm import relationship

from database import Base


def trunc_content(s):
    s.replace('\r', '').replace('\n', '')

    if len(s) > 25:
        s = s[:25] + "..."

    return s


class EmailJob(Base):
    __tablename__ = 'emailtasks'

    id = Column(Integer, primary_key=True)

    dest_address = Column(String(256))

    message_subject = Column(Text)
    message_content = Column(Text)

    status = Column(Enum('IN_PROGRESS', 'FAILED', 'COMPLETED', name='emailjob_status'), default='IN_PROGRESS')

    emails = relationship('Email', backref='job')

    def __repr__(self):
        return "[Job with status %s to message '%s' with subject '%s' and content '%s']" % (
            self.status,
            self.dest_address,
            self.message_subject,
            trunc_content(self.message_content),
        )


class RandomB64StringGenerator:
    def __init__(self):
        self.charset = ['-', '_']

        for a, b in (('a', 'z'), ('A', 'Z'), ('0', '9')):
            for c in [chr(i) for i in xrange(ord(a), ord(b) + 1)]:
                self.charset.append(c)

    def get_random_string(self, length):
        return ''.join([choice(self.charset) for _ in xrange(length)])


class Email(Base):
    __tablename__ = 'emails'

    id = Column(Integer, primary_key=True)

    uid = Column(String(32))

    dest_address = Column(String(256))

    subject = Column(Text)
    content = Column(Text)

    status = Column(Enum('ENQUEUED', 'SENT', 'OPENED', 'SPAM', name='email_status'), default='ENQUEUED')

    last_update = Column(DateTime)

    job_id = Column(Integer, ForeignKey(EmailJob.id))

    uidGen = RandomB64StringGenerator()

    def __init__(self, **kwargs):
        # Generate a random unique id to identify the email in notify URLs

        self.uid = self.uidGen.get_random_string(32)
        self.last_update = datetime.now()

        super(Email, self).__init__(**kwargs)

    def __repr__(self):
        return "[Email with status %s to %s with subject '%s' and content '%s', last updated %s, with unique id %s]" % (
            self.status,
            self.dest_address,
            self.subject,
            trunc_content(self.content),
            self.last_update,
            self.uid
        )
