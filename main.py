from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask import send_from_directory
import os
import yagmail
import string
import random
from hashutils import make_pw_hash, check_pw_hash

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")

app.config['SQLALCHEMY_ECHO'] = True

#been awhile?
#. ../../config.sh
#that first lone dot is like the sh command, i think
#. ./venv/bin/activate
#put some topsecret info in config.sh, stuff that doesn't go on github

#learn the delete button at get-it-done #3
#flask migrate get-it-done #4
#alter a table without dropping and recreating
#flash message categories video #8

db = SQLAlchemy(app)
app.secret_key = os.getenv("SECRET_KEY")

class Sink(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  location = db.Column(db.String(120))
  downloads = db.Column(db.Integer)
  donor_id = db.Column(db.Integer, db.ForeignKey('donator.id'))
  #not really sure how to utilize backref, need to read up on that
  elephant = db.relationship('Rating', backref="ratified")
  
  def __init__(self, location, donor):
    self.location=location
    self.downloads=0
    self.donor = donor

class Donator(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  location = db.Column(db.String(60))
  #backref again, could probably utilize this for simpler code
  elephant = db.relationship('Sink', backref="donor")
  
  def __init__(self, location):
    self.location=location
    
class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(20), unique=True)
  hashpass = db.Column(db.String(70))
  email = db.Column(db.String(60), unique=True)
  company = db.Column(db.String(60))
  catchphrase = db.Column(db.String(60))
  state = db.Column(db.String(2))
  #could recycle this for new polls.  or use mod to store multiple info.
  dustmask = db.Column(db.Integer)
  benefactor = db.Column(db.Integer)  #i think i stored downloads here
  lastsink = db.Column(db.Integer)
  #again could use the mod trick.  would need to fix all the color coding.
  #could probably move all that to a function somewhere
  memberlevel = db.Column(db.Integer)
  #double backref.  sigh.
  elephant = db.relationship('Rating', backref="rater")
  tiger = db.relationship('Babblings', backref="babbler")
  
  def __init__(self, username, password, email, company, catchphrase, state, dustmask):
    self.username=username
    self.hashpass=make_pw_hash(password)
    self.email=email
    self.company=company
    self.catchphrase=catchphrase
    self.state=state
    self.dustmask=dustmask
    self.benefactor=0
    self.lastsink=0
    self.memberlevel=0
    
class Rating(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  stars = db.Column(db.Integer)
  comment = db.Column(db.String(60))
  #so this is many-to-many without realizing it
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
  sink_id = db.Column(db.Integer, db.ForeignKey('sink.id'))
  
  def __init__(self, stars, comment, rater, ratified):
    self.stars=stars
    self.comment=comment
    self.rater=rater        #user_id?
    self.ratified=ratified  #sink_id?
    
class Babblings(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
  babble = db.Column(db.String(60))
  
  def __init__(self, babble, babbler):
    self.babbler=babbler
    self.babble=babble

#haven't even bothered to understand this just ripped from stack overflow
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
  return ''.join(random.choice(chars) for _ in range(size))

def cadchecker(cadfile):
  if (cadfile.lower().endswith('.dxf') or cadfile.lower().endswith('.dwg') or
      cadfile.lower().endswith('.ard') or cadfile.lower().endswith('.asd') or
      cadfile.lower().endswith('.tag') or cadfile.lower().endswith('.est')):
    return True
  else:
    return False

#global variables
#session['searchval']
#session['blanco']
#session['donor']
#session['current_folder']
#session['username']
#session['secret_pass']
#session['password']

#set donorval to "" to set back to silicatewastes
#set cloneguys to "" to clear it.  silly but whatever
def initialize(donorval, cloneguys):
  loadguys=Donator.query.all()
  
  guys=[]
  for ix in range(len(loadguys)):
    guys.append(loadguys[ix].location)

  #should probably put a check here that all cloneguys in guys
  if not donorval:
    if len(guys)>0:
      donor=guys[0]
    else:
      donor=""
  else:
    if len(guys)>0 and donorval in guys:
      donor=donorval
    else:
      donor=""
      cloneguys=""
    
  return (guys, donor, cloneguys)

#so reset is just for searchvals, initialize is... something else
def reset():
  session['searchval']=""
  session['blanco']=""

#this just grabs a sink location and chops off the donor and folder
#returns truncated location and the sink row
#sets donor and current_folder
def sinksplit(sinkid):
  entry = Sink.query.filter_by(id=sinkid).first()
  #try:
       # session['donor']=Donator.query.filter_by(location=newdonor).first().location
      #except Exception as e:
  try:
    cad = entry.location
  except Exception as e:
    flash("Can't find sink.  Stop messing with the URL.")
    entry = Sink.query.filter_by(id=1).first()
    cad = entry.location
  
  cadsplit = cad.split(os.path.sep)
  skip=False
  
  session['donor']=cadsplit[0]
  
  #if no base folders
  for root, dirs, files in os.walk(os.path.join("static","sinks",cadsplit[0]), topdown=True):
    if len(dirs) == 0:
      skip=True
    break
  
  if not skip:
    sink=cadsplit[2]
    for ix in range(len(cadsplit)-3):
      sink+=(os.path.sep+cadsplit[3+ix])
    session['current_folder']=cadsplit[1]
  else:
    sink=cadsplit[1]
    for ix in range(len(cadsplit)-2):
      sink+=(os.path.sep+cadsplit[2+ix])
    session['current_folder']=""
  
  return (sink, entry)
  
@app.before_request
def require_login():
  allowed_routes = ['index', 'login', 'register', 'stats', 'verify', 'stalk', 'demos']
  #need that '/static/' part for css i think
  if (request.endpoint not in allowed_routes and 'username' not in session and
    '/static/' not in request.path):
    
    flash("log in")
    
    return redirect('/')
  
##############################///////////////////////////########################################
##############################///////////////////////////########################################
##############################///////////////////////////########################################
##############################///////////////////////////########################################
##############################///////////////////////////########################################
##############################///////////////////////////########################################
##############################///////////////////////////########################################
##############################///////////////////////////########################################

#1st column list of all donors
#guys=[]
#session['donor']=""
#cloneguys=[]

#2nd column all the folders in the donor's root directory
#folders=[]
#session['current_folder']=""

#3rd column
#initial_files=[]

#session['searchval']=""
#session['blanco']=""
#blancopackage=""

#session['secret_pass']=""

@app.route('/', methods=['GET'])
def index():
  #this if might end up pointless
  if request.method == 'GET':
    ix=5

  return render_template('silicate.html',title="silicatewastes")
  
if __name__ == '__main__':
  app.run()

