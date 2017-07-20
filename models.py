from sqlalchemy import Column, ForeignKey, Integer, String, Text, Enum, DateTime
from sqlalchemy.orm import relationship

from database import Base


def trunc_content(s):
    s.replace('\r', '').replace('\n', '')

    if len(s) > 25:
        s = s[:25] + "..."

    return s


class EmailTask(Base):
    __tablename__ = 'emailtasks'

    id = Column(Integer, primary_key=True)

    dest_address = Column(String(256))

    message_subject = Column(Text)
    message_content = Column(Text)

    status = Column(Enum('SCHEDULED', 'IN_PROGRESS', 'FAILED', 'COMPLETED', name='emailtask_status'), default='SCHEDULED')

    emails = relationship('Email', backref='task')

    def __repr__(self):
        return "[Task with status %s to message '%s' with subject '%s' and content '%s']" % (
            self.status,
            self.dest_address,
            self.message_subject,
            trunc_content(self.message_content),
        )

class Email(Base):
    __tablename__ = 'emails'

    id = Column(Integer, primary_key=True)

    dest_address = Column(String(256))

    subject = Column(Text)
    content = Column(Text)

    status = Column(Enum('SCHEDULED', 'SENT', 'OPENED', 'SPAM', name='email_status'), default='SCHEDULED')

    sent_date = Column(DateTime)

    task_id = Column(Integer, ForeignKey(EmailTask.id))

    def __repr__(self):

        return "[Task with status %s to %s with subject '%s' and content '%s']" % (
            self.status,
            self.dest_address,
            self.message_subject,
            trunc_content(self.message_content),
        )
