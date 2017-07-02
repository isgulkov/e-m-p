from sqlalchemy import Column, Integer, String, Text

from database import Base


class EmailTask(Base):
    __tablename__ = 'emailtasks'

    id = Column(Integer, primary_key=True)

    dest_address = Column(String(256))

    message_subject = Column(Text)
    message_content = Column(Text)

    def __repr__(self):
        def trunc_content(s):
            s.replace('\r', '').replace('\n', '')

            if len(s) > 25:
                s = s[:25] + "..."

            return s

        return "[Task to message '%s' with subject '%s' and content '%s']" % (
            self.dest_address,
            self.message_subject,
            trunc_content(self.message_content),
        )
