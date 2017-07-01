#coding: utf-8

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import DataRequired, Email


class NewTaskForm(FlaskForm):
    dest_address = StringField(u"Адрес назначения", validators=[DataRequired(), Email()])

    message_subject = StringField(u"Тема сообщения", validators=[DataRequired()])
    message_text = TextAreaField(u"Текст сообщения", validators=[DataRequired()])
