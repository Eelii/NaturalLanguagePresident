from flask import Flask, render_template, redirect, session, flash, abort, request
from flask_wtf import FlaskForm

#form imports
from wtforms import StringField, IntegerField, RadioField, SubmitField, PasswordField, validators, Flags

#Used to automatically create a form based on a class 
from wtforms.ext.sqlalchemy.orm import model_form

from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy.orm import relationship

from werkzeug.security import generate_password_hash, check_password_hash

import natural_language_president as nlp
import datetime

ai = nlp.init_ai()

app = Flask(__name__)
#TODO
app.secret_key = 'fdsAf.ADfeqqvb.oirKIOGdafa'
db = SQLAlchemy(app)

#app.jinja_env.globals["currentUser"] = currentUser????????????????


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username =  db.Column(db.String, nullable=False, unique=True)
    email = db.Column(db.String, nullable=False, unique=True)
    passwordHash = db.Column(db.String, nullable=False)

    def setPassword(self, password):
        self.passwordHash = generate_password_hash(password)

    def checkPassword(self, password):
        return check_password_hash(self.passwordHash, password)

class UserForm(FlaskForm):
    username = StringField('username', validators=[validators.InputRequired()])
    email = StringField('email', validators=[validators.Email()])
    password = PasswordField('password', validators=[validators.InputRequired()])

class Tweet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String, nullable=False)
    rating = db.Column(db.Integer)
    dateTime = db.Column(db.String)
    generatedBy = db.Column(db.String)
    adderallLevel = db.Column(db.Integer)
    prompt = db.Column(db.String)
    totalRating = db.Column(db.Integer)
    ratings = relationship('Rating')

    def updateTotalRating(self):
        if  Rating.query.filter(Rating.tweet_id==self.id).all():
            tweetRatings = Rating.query.filter(Rating.tweet_id==self.id).all()
            totalRating = 0
            for rating in tweetRatings:
                totalRating += rating.rating
            self.totalRating = totalRating
        else:
            pass

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    user = db.Column(db.String, nullable=False)
    tweet_id = db.Column(db.Integer, db.ForeignKey('tweet.id'))
    parent = relationship("Tweet", back_populates="ratings")

class TweetForm(FlaskForm):
    adderallLevel = RadioField('Sanity Level', choices=[('1','Relatively Normal'),('3',"Cola'd-up"), ('5','MAGAnificent'), ('7','Sleep Deprived'), ('99','Complete Lunacy')], default='5')
    #adderallLevel = IntegerField('Sleep deprivation level', validators=[validators.Optional()])
    prompt = StringField('Prompt (optional)', validators=[validators.Optional()])

def createTweet(prompt=None, adderallLevel=None):
    tweet = Tweet()
    tweet.dateTime = str(datetime.datetime.now().strftime('%H:%M:%S %d.%m.%Y'))
    tweet.adderallLevel = int(adderallLevel)/10
    tweet.prompt = prompt

    if prompt and adderallLevel:
        #Transformers only accepts temperature values in a float format (usually in the range 0.1-0,9).
        tweet.text = nlp.generateTweet(ai, prompt=prompt, temperature=tweet.adderallLevel)
    elif prompt:
        tweet.text = nlp.generateTweet(ai, prompt=prompt)
    elif adderallLevel:
        tweet.text = nlp.generateTweet(ai, temperature=tweet.adderallLevel)
    else:
        tweet.text = nlp.generateTweet(ai)
    print(tweet.adderallLevel)
    print(tweet.prompt)
   # print('Created: ' + str(tweet.adderallLevel) + tweet.prompt)
    return tweet
        


##??????????
def currentUser():
	try:
		uid = int(session["uid"])
	except:
		return None
	return User.query.get(uid)

def loginRequired():
    if not currentUser():
        abort(403)

app.jinja_env.globals['currentUser'] = currentUser

@app.before_first_request
def init_db():
    db.create_all()
    user = User(username='admin', email='admin@example.com')
    user.setPassword('admin')
    db.session.add(user)
    db.session.commit()

@app.route('/register', methods=['POST', 'GET'])
def register():
    form = UserForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data

        if User.query.filter_by(username=username).first():
            flash('Username is already taken :(')
            return redirect('/register')
        
        elif User.query.filter_by(email=email).first():
            flash('email is already registered for a user.')
            return redirect('/register')

        else:
            user = User(username=username, email=email)
            user.setPassword(password)
            db.session.add(user)
            db.session.commit()
            flash('Registration successfull!')
            return redirect('/login')
    return render_template("register.html", form=form, title='Register')

@app.route('/login', methods=['POST', 'GET'])
def login():
    form = UserForm() 
    #TODO
    ##form.email.flags=Flags.hidden
    # When a user presses the submit button in a form, validate_on_submit method will return True.
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()

        if not user:
                flash('Login failed')
                #TODO
                print('Login failed')
                return redirect('/login')

        if not user.checkPassword(password):
                flash('Login failed. SAD!')
                #TODO
                print('Password failed')
                return redirect('/login')
        session["uid"]=user.id
        flash('Login successfull')
        return redirect('/')

    return render_template('login.html', form=form, title='Please log in')

@app.route('/logout')
def logoutView():
        session['uid'] = None
        flash("...and you're fired!")
        return redirect('/login')

@app.route('/', methods=['POST', 'GET'])
def mainPage():
    # An alternative to loginRequired(). Used for redirection to login page. 
    '''if not currentUser():
        print('forbidden')
        return redirect('/login')'''

    for tweet in Tweet.query.all():
        tweet.updateTotalRating()

    tweets = Tweet.query.all()

    tweet = Tweet()
    form = TweetForm()
    if form.validate_on_submit():
        if form.data:
            tweet = createTweet(form.prompt.data, form.adderallLevel.data)
        else:
            tweet = createTweet()
        print('FORM: ' + form.prompt.data + str(form.adderallLevel.data))

        '''
        ratings = Rating.query.all()
        for rating in ratings:
            print('Rating: ' + str(rating.rating))
            print('User: ' + rating.user)
            print('Tweet ID: ' + str(rating.tweet_id))
        '''

        db.session.add(tweet)
        db.session.commit()
        return redirect('/')

    return render_template("mainPage.html", tweets=tweets, title='The Greatest Main Page', form=form)

@app.route('/upvote/<int:tweetId>', methods=['GET', 'POST'])
def upvote(tweetId):
    loginRequired()
    username = currentUser().username
    ratings = Rating.query.all()
    userHasVoted = False
    for rating in ratings:
        if rating.user == username and rating.tweet_id == tweetId:
            userHasVoted = True
    if not userHasVoted:
        rating = Rating(tweet_id=tweetId, user=username, rating=1)
        db.session.add(rating)
        db.session.commit()
        return redirect('/')
    else:
        abort(403)

@app.route('/downvote/<int:tweetId>', methods=['GET', 'POST'])
def downvote(tweetId):
    loginRequired()
    username = currentUser().username
    ratings = Rating.query.all()
    userHasVoted = False
    for rating in ratings:
        if rating.user == username and rating.tweet_id == tweetId:
            userHasVoted = True
    if not userHasVoted:
        rating = Rating(tweet_id=tweetId, user=username, rating=-1)
        db.session.add(rating)
        db.session.commit()
        return redirect('/')
    else:
        abort(403)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', title='Page not found, loser!'), 404

if __name__ == '__main__':
    app.run()
