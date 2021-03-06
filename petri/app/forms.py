__author__ = 'max'
from flask import flash
from flask.ext.wtf import Form
from wtforms import TextField, BooleanField, TextAreaField, validators, PasswordField, SubmitField
from wtforms.validators import Required, Length, ValidationError
from models import User, Phonenumbers
import string

all = string.maketrans('', '')
nodigs = all.translate(all, string.digits)

class LoginForm(Form):
    email = TextField("Email", [validators.Required("Please enter your email address."),
                                validators.Email("Please a valid email address.")])
    password = PasswordField('Password', [validators.Required("Please enter a password.")])
    remember_me = BooleanField('Remember me', default=False)
    submit = SubmitField("Sign In")

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        user = User.query.filter_by(email=self.email.data.lower()).first()
        if user and user.check_password(self.password.data):
            return True
        else:
            self.email.errors.append("Invalid e-mail or password")
            return False

# custom validator

class _number(object):
    def __init__(self, message=None):
        if not message:
            message = u'Field must be between %i and %i characters long and a number.' % (min, max)
        self.message = message

    def __call__(self, form, field):
        l = str(field.data)
        if not l.isdigit():
            raise ValidationError(self.message)

class SignupForm(Form):
    firstname = TextField("First name", [validators.Required("Please enter your first name.")])
    lastname = TextField("Last name", [validators.Required("Please enter your last name.")])
    email = TextField("Email", [validators.Required("Please enter your email address."),
                                validators.Email("Please a valid email address.")])
    phonenumber = TextField("Phone number", [validators.Required("Please enter a phone number."),
                                             validators.Length(min=10, max=12, message=("Phone number must be 10 digits long"))])
    keycode = PasswordField("4 digit Key Code for signing into the phone menu", [validators.Required("Please enter a key code"),
                                         _number("Key code must be a number"),
                                         validators.Length(min=4, max=4, message=("Key Code is incorrect length"))])
    password = PasswordField('Password', [validators.Required("Please enter a password.")])
    submit = SubmitField("Create account")

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False

        user = User.query.filter_by(email=self.email.data.lower()).first()
        if user:
            self.email.errors.append("That email is already taken")
            return False
        user = None
        user = User.query.filter_by(phonenumber=self.phonenumber.data.lower()).first()
        if user:
            self.phonenumber.errors.append("That phone number is already taken")
            return False
        else:
            return True

class EditForm(Form):
    nickname = TextField('nickname', validators=[Required()])
    about_me = TextAreaField('about_me', validators=[Length(min=0, max=140)])

    def __init__(self, original_nickname, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.original_nickname = original_nickname

    def validate(self):
        if not Form.validate(self):
            return False
        if self.nickname.data == self.original_nickname:
            return True
        user = User.query.filter_by(nickname=self.nickname.data).first()
        if user != None:
            self.nickname.errors.append('This nickname is already in use. Please choose another one.')
            return False
        return True


class PostForm(Form):
    post = TextField('post', validators=[Required()])


class AddNumberForm(Form):
    firstname = TextField("First name", [validators.Required("Please enter your first name.")])
    lastname = TextField("Last name", [validators.Required("Please enter your last name.")])
    phonenumber = TextField("Phone number", [validators.Required("Please enter a phone number."),
                                             validators.Length(min=10, max=12,
                                                               message=("Phone number must be 10 digits long"))])
    submit = SubmitField("Add number")

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)

    def validate(self):
        if not Form.validate(self):
            return False
        cleanPhoneNumber = str(self.phonenumber.data).translate(all, nodigs)
        number = Phonenumbers.query.filter_by(firstname=self.firstname.data.title()).filter_by(lastname=self.lastname.data.title()).filter_by(
            number=cleanPhoneNumber).first()
        if number :
            flash('Person has already been entered.')
            return False
        return True


class ContactForm(Form):
    firstname = TextField("First name", [validators.Required("Please enter your first name.")])
    lastname = TextField("Last name", [validators.Required("Please enter your last name.")])
    email = TextField("Email", [validators.Required("Please enter your email address."),
                                validators.Email("Please a valid email address.")])
    message = TextField('post', validators=[Required()])

    def __init__(self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)