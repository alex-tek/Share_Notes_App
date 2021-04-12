# FLASK Tutorial 1 -- We show the bare bones code to get an app up and running

# imports
import os  # os is used to get environment variables IP & PORT
from flask import Flask  # Flask is the web app that we will customize
from flask import render_template
from flask import request
from flask import redirect, url_for
from database import db
from models import Note as Note
from models import User as User
from forms import RegisterForm
from flask import session
import bcrypt
from forms import RegisterForm, LoginForm, CommentForm, ShareForm, HighLightForm
from models import Comment as Comment
from models import Homework as Homework

app = Flask(__name__)  # create an app
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///note_note_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'SE3155'
#  Bind SQLAlchemy db object to this Flask app
db.init_app(app)
# Setup models
with app.app_context():
    db.create_all()  # run under the app context

the_user = False
user_log = []
budget_error = False
# @app.route is a decorator. It gives the function "index" special powers.
# In this case it makes it so anyone going to "your-url/" makes this function
# get called. What it returns is what is shown as the web page
@app.route('/')
@app.route('/index')
def index():
    # check if a user is saved in session
    if session.get('user'):
        return render_template("index.html", user=session['user'])
    return render_template("index.html")


@app.route('/notes')
def get_notes():
    # check if a user is saved in session
    if session.get('user'):
        # retrieve notes from database
        my_notes = db.session.query(Note).filter_by(user_id=session['user_id']).all()

        return render_template('notes.html', notes=my_notes, user=session['user'])
    else:
        return redirect(url_for('login'))


@app.route('/notes/<note_id>')
def get_note(note_id):
    # check if a user is saved in session
    if session.get('user'):
        # retrieve notes from database
        my_note = db.session.query(Note).filter_by(id=note_id, user_id=session['user_id']).one()

        # create a comment form object
        form = CommentForm()

        return render_template('note.html', note=my_note, user=session['user'], form=form)
    else:
        return redirect(url_for('login'))


@app.route('/notes/new', methods=['GET', 'POST'])
def new_note():
    # check if a user is saved in session
    if session.get('user'):
        if request.method == 'POST':
            # get title data
            title = request.form['title']
            # get note data
            text = request.form['noteText']
            # create date stamp
            from datetime import date
            today = date.today()
            # format date mm/dd/yyyy
            today = today.strftime('%m-%d-%y')
            # create new note entry
            new_record = Note(title, text, today, session['user_id'])
            db.session.add(new_record)
            db.session.commit()

            return redirect(url_for('get_notes'))

        else:
            # GET request - show new note form
            return render_template('new.html', user=session['user'])
    else:
        # user is not in session redirect to login
        return redirect(url_for('login'))


@app.route('/notes/edit/<note_id>', methods=['GET', 'POST'])
def update_note(note_id):
    # check if a user is saved in session
    if session.get('user'):
        if request.method == 'POST':
            # get title data
            title = request.form['title']
            # get note data
            text = request.form['noteText']
            note = db.session.query(Note).filter_by(id=note_id).one()
            # update note data
            note.title = title
            note.text = text
            # update note in DB
            db.session.add(note)
            db.session.commit()

            return redirect(url_for('get_notes'))
        else:
            # retrieve note from database
            my_note = db.session.query(Note).filter_by(id=note_id).one()

        return render_template('new.html', note=my_note, user=session['user'])
    else:
        # user is not in session redirect to login
        return redirect(url_for('login'))


@app.route('/notes/delete/<note_id>', methods=['GET', 'POST'])
def delete_note(note_id):
    # check if a user is saved in session
    if session.get('user'):
        # retrieve note form database
        my_note = db.session.query(Note).filter_by(id=note_id).one()
        db.session.delete(my_note)
        db.session.commit()

        return redirect(url_for('get_notes'))

    # user is not in session redirect to login
    return redirect(url_for('login'))


@app.route('/register', methods=['POST', 'GET'])
def register():
    form = RegisterForm()
    # validate_on_submit only validates using POST
    if form.validate_on_submit():
        # form validation included a criteria to check the username does not exist
        # we can know we are safe to add the other user to the database
        password_hash = bcrypt.hashpw(request.form['password'].encode('utf-8'),bcrypt.gensalt())
        first_name = request.form['firstname']
        last_name = request.form['lastname']
        new_record = User(first_name, last_name, request.form['email'], password_hash)
        db.session.add(new_record)
        db.session.commit()
        # save the user's name to the session
        session['user'] = first_name
        # get the id of the newly created database record
        the_user = db.session.query(User).filter_by(email=request.form['email']).one()
        # save the user's id to the session
        session['user_id'] = the_user.id

        return redirect(url_for('get_notes'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
    login_form = LoginForm()
    # validate_on_submit only validates using POST
    if login_form.validate_on_submit():
        # we know user exists. We can use one()
        the_user = db.session.query(User).filter_by(email=request.form['email']).one()
        # user exists check password entered matches stored password
        if bcrypt.checkpw(request.form['password'].encode('utf-8'), the_user.password):
            # password match add user info to session
            session['user'] = the_user.first_name
            session['user_id'] = the_user.id
            # render view
            return redirect(url_for('get_notes'))

        # password check failed
        # set error message to alert user
        login_form.password.errors = ["Incorrect username or password."]
        return render_template("login.html", form=login_form)
    else:
        # form did not validate or GET request
        return render_template("login.html", form=login_form)


@app.route('/logout')
def logout():
    # check if a user is saved in session
    if session.get('user'):
        session.clear()

    return redirect(url_for('index'))


@app.route('/notes/<note_id>/comment', methods=['POST'])
def new_comment(note_id):
    if session.get('user'):
        comment_form = CommentForm()
        # validate_on_submit only validates using POST
        if comment_form.validate_on_submit():
            # get comment data
            comment_text = request.form['comment']
            new_record = Comment(comment_text, int(note_id), session['user_id'])
            db.session.add(new_record)
            db.session.commit()

        return redirect(url_for('get_note', note_id=note_id))

    else:
        return redirect(url_for('login'))


@app.route('/about')
def about():
    # check if a user is saved in session
    if session.get('user'):
        return render_template("about.html", user=session['user'])
    return render_template("about.html")


@app.route('/contact')
def contact():
    # check if a user is saved in session
    if session.get('user'):
        return render_template("contact.html", user=session['user'])
    return render_template("contact.html")


@app.route('/notes/<note_id>/comment/delete/<comment_id>', methods=['POST'])
def delete_comment(note_id, comment_id):
    if session.get('user'):
        # get comment from the database
        my_comment = db.session.query(Comment).filter_by(id=comment_id).one()
        db.session.delete(my_comment)
        db.session.commit()

        return redirect(url_for("get_note", note_id=note_id))
    else:
        return redirect(url_for('login'))


@app.route('/sharing', methods=['POST', 'GET'])
def sharing():
    share_form = ShareForm()
    if share_form.validate_on_submit():
        the_user = db.session.query(User).filter_by(email=request.form['email'])
  
        return redirect(url_for('get_notes'))

        # return render_template("sharing.html", form=share_form)
    else:
        
        return render_template("sharing.html", form=share_form)
            
    # return redirect(url_for('get_notes'))


@app.route('/notes/<note_id>', methods=['POST'])
def highlight(note_id):
    highlight_form = HighLightForm()
   
    my_note = db.session.query(Note).filter_by(id=note_id).one()

    return render_template("sharing.html", form=highlight_form)


@app.route('/homework')
def homework():
    if session.get('user'):
      incomplete = Homework.query.filter_by(complete=False).all()
      complete = Homework.query.filter_by(complete=True).all()

      return render_template('homework.html', incomplete=incomplete, complete=complete)
    else:
        return redirect(url_for('login'))


@app.route('/add', methods=['POST'])
def add():
    item = Homework(text=request.form['homework-item'], complete=False)
    db.session.add(item)
    db.session.commit()

    return redirect(url_for('homework'))


@app.route('/complete/<id>')
def complete(id):

    item = Homework.query.filter_by(id=int(id)).first()
    item.complete = True
    db.session.commit()

    return redirect(url_for('homework'))
@app.route('/complete/delete/<id>')
def delete(id):

    item = Homework.query.filter_by(id=int(id)).first()
    item.complete = True
    db.session.delete(item)
    db.session.commit()

    return redirect(url_for('homework'))






app.run(host=os.getenv('IP', '127.0.0.1'), port=int(os.getenv('PORT', 5000)), debug=True)

# To see the web page in your web browser, go to the url,
#   http://127.0.0.1:5000

# Note that we are running with "debug=True", so if you make changes and save it
# the server will automatically update. This is great for development but is a
# security risk for production.
