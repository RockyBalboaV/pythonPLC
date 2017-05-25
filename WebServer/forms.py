# coding=utf-8
from flask_wtf import FlaskForm
from wtforms import (
    widgets,
    StringField,
    TextAreaField,
    PasswordField,
    BooleanField,
    SubmitField,
)
from wtforms.validators import DataRequired, length, EqualTo, URL, Email


class CKTextAreaWidget(widgets.TextArea):
    def __call__(self, field, **kwargs):
        kwargs.setdefault('class_', 'ckeditor')
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)


class CKTextAreaField(TextAreaField):
    widgets = CKTextAreaWidget()


class LoginForm(FlaskForm):
    username = StringField('Username', [DataRequired(), length(min=4, max=25)])
    password = PasswordField('Password', [DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField('Submit')



class RegistrationForm(FlaskForm):
    username = StringField('Username', [DataRequired(), length(min=4, max=25)])
    email = StringField('Email Address', [length(min=4, max=35)])
    password = PasswordField('New Password', [DataRequired(), EqualTo('confirm', message='Password must match')])
    confirm = PasswordField('Repeat Password')
