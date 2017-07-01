from flask_wtf import Form
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Email


class NewTaskForm(Form):
    # TODO: translate labels to Russian
    dest_address = StringField("Destination address", validators=[DataRequired(), Email()])

    message_subject = StringField("Message subject", validators=[DataRequired()])
    message_text = TextAreaField("Message text", validators=[DataRequired()])
