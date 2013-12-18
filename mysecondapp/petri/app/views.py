
__author__ = 'max'
from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid
from forms import LoginForm, EditForm, PostForm, SignupForm, AddNumberForm
from models import User, ROLE_USER, ROLE_ADMIN, Phonenumbers
from datetime import datetime
from config import NUMBERS_PER_PAGE
from emails import follower_notification
import twilio.twiml
import string
# before database request!!!
@app.before_request
def before_request():
    g.user = current_user
    if g.user.is_authenticated():
        g.user.last_seen = datetime.utcnow()
        db.session.add(g.user)
        db.session.commit()


@app.route('/twilio', methods=['GET', 'POST'])
@app.route('/twilio/<int:id>', methods=['POST'])
def get_number(id=0):
    resp = twilio.twiml.Response()
    if request.method == 'GET':
        with resp.gather(numDigits=10, action="/twilio", method="POST") as r:
            r.say("Enter your phone number.")
        return str(resp)
    elif request.method == 'POST':
        if id == 0:
            digit_pressed = request.values.get('Digits', None)
            user = User.query.filter_by(phonenumber=str(digit_pressed).lower()).first()
            if user:
                user_id = User.query.filter_by(phonenumber=str(digit_pressed).lower()).first().id
                with resp.gather(numDigits=4, action="/twilio_key/"+str(user_id), method="POST") as r:
                    r.say("Enter your 4 digit key code.")
                return str(resp)
            else:
                resp.say("That phone number doesn't exist. Please try again.")
                resp.redirect('/twilio', method='GET')
                return str(resp)
        else:
            with resp.gather(numDigits=4, action="/twilio_key/" + str(id), method="POST") as r:
                r.say("Enter your 4 digit key code.")
            return str(resp)

@app.route("/twilio_key/<int:id>", methods=['GET', 'POST'])
def handle_telnumber(id):
    """Handle key press from a user."""
    resp = twilio.twiml.Response()
    # Get the digit pressed by the user
    digit_pressed = request.values.get('Digits', None)
    user = User.query.get(id)
    if user and user.check_keycodehash(digit_pressed):
        phonenumbers = user.phonenumbers.all()
        for number in phonenumbers:
            resp.say(str(number.firstname))
            resp.say(str(number.lastname))
            for n in number.number:
                resp.say(str(n))
        resp.say("Good bye!")
        return str(resp)
    else:
        resp.say("Incorrect key code. Please try again.")
        resp.redirect("/twilio/"+str(id), method='POST')
    return str(resp)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = SignupForm()
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('home'))
    if request.method == 'POST':
        if form.validate() == False:
            # errors are automatically stored in the form and template has access to them
            return render_template('signup.html', form=form)
        else:

            all = string.maketrans('','')
            nodigs = all.translate(all, string.digits)
            cleanPhoneNumber = str(form.phonenumber.data).translate(all, nodigs)
            newuser = User(form.firstname.data, form.lastname.data, form.email.data, cleanPhoneNumber, form.keycode.data,
                           form.password.data)
            db.session.add(newuser)
            db.session.commit()
            session['email'] = newuser.email
            session['remember_me'] = True
            login_user(newuser)
            return redirect(url_for('home'))
    elif request.method == 'GET':
        return render_template('signup.html', form=form)


@app.route('/home', methods=['GET', 'POST'])
@app.route('/home/<int:page>', methods=['GET', 'POST'])
@login_required
def home(page = 1):
    info = str(g.user)
    # phonenumbers = g.user.phonenumbers.paginate(page, NUMBERS_PER_PAGE, False)
    phonenumbers = g.user.phonenumbers.all()
    # return str(phonenumbers[1])
    return render_template('home.html',
                           info=info,
                           remember=session['remember_me'],
                           phonenumbers=phonenumbers)

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('home'))
    form = LoginForm()
    if request.method == 'GET':
        return render_template('login.html', title='Sign in', form=form)
    if form.validate():
        session['remember_me'] = form.remember_me.data
        user = User.query.filter_by(email=form.email.data.lower()).first()
        login_user(user, remember=session['remember_me'] )
        return redirect(url_for('home'))
    return render_template('login.html',
                           title='Sign In',
                           form=form)

@app.route('/addnumber', methods=['GET', 'POST'])
@login_required
def addnumber():
    form = AddNumberForm()
    if request.method == 'GET':
        return render_template('addnumber.html', title='Add a phonenumber', form=form)
    if form.validate():
        phonenumber = Phonenumbers(firstname=form.firstname.data, lastname=form.lastname.data, number=form.phonenumber.data, owner=g.user)
        db.session.add(phonenumber)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('home'))
    return render_template('addnumber.html',
                           form=form)

#
# @oid.after_login
# def after_login(resp):
#     if resp.email is None or resp.email == "":
#         flash('Invalid login. Please try again.')
#         redirect(url_for('login'))
#     user = User.query.filter_by(email=resp.email).first()
#     if user is None:
#         nickname = resp.nickname
#         if nickname is None or nickname == "":
#             nickname = resp.email.split('@')[0]
#         nickname = User.make_unique_nickname(nickname)
#         user = User(nickname=nickname, email=resp.email, role=ROLE_USER)
#         db.session.add(user)
#         db.session.commit()
#         # make the user follow him/herself
#         # db.session.add(user.follow(user))
#         # db.session.commit()
#     remember_me = False
#     if 'remember_me' in session:
#         remember_me = session['remember_me']
#         session.pop('remember_me', None)
#     login_user(user, remember=remember_me)
#     return redirect(request.args.get('next') or url_for('home'))

#
# @app.route('/follow/<nickname>')
# @login_required
# def follow(nickname):
#     user = User.query.filter_by(nickname=nickname).first()
#     if user == None:
#         flash('User ' + nickname + ' not found.')
#         return redirect(url_for('home'))
#     if user == g.user:
#         flash('You can\'t follow yourself!')
#         return redirect(url_for('user', nickname=nickname))
#     u = g.user.follow(user)
#     if u is None:
#         flash('Cannot follow ' + nickname + '.')
#         return redirect(url_for('user', nickname=nickname))
#     db.session.add(u)
#     db.session.commit()
#     flash('You are now following ' + nickname + '!')
#     follower_notification(user, g.user)
#     return redirect(url_for('user', nickname=nickname))
#
#
# @app.route('/unfollow/<nickname>')
# def unfollow(nickname):
#     user = User.query.filter_by(nickname=nickname).first()
#     if user == None:
#         flash('User ' + nickname + ' not found.')
#         return redirect(url_for('home'))
#     # if user == g.user:
#     #     flash('You can\'t unfollow yourself!')
#     #     return redirect(url_for('user', nickname=nickname))
#     u = g.user.unfollow(user)
#     if u is None:
#         flash('Cannot unfollow ' + nickname + '.')
#         return redirect(url_for('user', nickname=nickname))
#     db.session.add(u)
#     db.session.commit()
#     flash('You have stopped following ' + nickname + '.')
#     return redirect(url_for('user', nickname=nickname))




@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    form = EditForm(g.user.nickname)
    if form.validate_on_submit():
        g.user.nickname = form.nickname.data
        g.user.about_me = form.about_me.data
        db.session.add(g.user)
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit'))
    else:
        form.nickname.data = g.user.nickname
        form.about_me.data = g.user.about_me
    return render_template('edit.html',
                           form=form)



@app.errorhandler(404)
def internal_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

