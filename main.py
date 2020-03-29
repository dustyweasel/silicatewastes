#ALTER TABLE sink
#ADD avg_rating float; 

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

##########model stuff that i should move to another file###################################
##########model stuff that i should move to another file###################################
##########model stuff that i should move to another file###################################
##########model stuff that i should move to another file###################################
##########model stuff that i should move to another file###################################
##########model stuff that i should move to another file###################################
##########model stuff that i should move to another file###################################
##########model stuff that i should move to another file###################################

db = SQLAlchemy(app)
app.secret_key = os.getenv("SECRET_KEY")

class Sink(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  location = db.Column(db.String(120))
  downloads = db.Column(db.Integer)
  donor_id = db.Column(db.Integer, db.ForeignKey('donator.id'))
  avg_rating = db.Column(db.Float)
  #not really sure how to utilize backref, need to read up on that
  elephant = db.relationship('Rating', backref="ratified")
  
  def __init__(self, location, donor):
    self.location=location
    self.downloads=0
    self.donor = donor
    self.avg_rating = 0.0

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

################################helper functions#######################################
################################helper functions#######################################
################################helper functions#######################################
################################helper functions#######################################
################################helper functions#######################################
################################helper functions#######################################
################################helper functions#######################################
################################helper functions#######################################

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
#def reset():
#  session['searchval']=""
#  session['blanco']=""

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

#expects a tuple with [2] set to avg rating
def getratecolor(val):
  if val < 1:
    color = "transparent"
  elif val >= 2:
    color = "mediumaquamarine"
  elif val >= 1.5:
    color = "orange"
  elif val < 1.5:
    color = "tomato"
    
  return color

def getselectcolor(val):
  if val=="":
    color="#f4f4f0"
  elif val=="search":
    color="lightblue"
  elif val=="blanco":
    color="lightgreen"
  else:
    color="red"
    
  return color
  
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

#setting this up so any donor folder either has all files in main folder or in subfolders.  if
#any subfolders are detected that all files in donor folder are ignored

#i think this will crash if the file system doesn't exist or whatever.  
#i'm not checking for it yet.  who cares.
@app.route('/', methods=['GET'])
def index():
  if request.method == 'GET':
    cads=[]
    if 'searchval' not in session:
      session['searchval']=""
    if 'state' not in session:
      session['state']=""
    
    #mode for forcing user to only make one decision at a time
    #state for if in searchmode or whatever
    #(mode can be "donor" but still be in search "state")
    mode="none"
    
    #was gonna make "state" too but just check if session['searchval'] for now
    #i'm gonna use 'mode' to set what i'm doing throughout '/', don't let the user
    #do two things at once but doing a lot of stuff regardless of 'mode'.  'mode' will
    #be a gatekeeper to certain statements
    
    #set "mode"
    if request.args.get('home') != None and request.args.get('home') == 'search':
      mode="search"
      #need to make sure if 'home' == 'search' then form sends back 'searchval' too
      #not checking for session['searchval'] != None
      session['searchval'] = request.args.get('searchval')
      if len(session['searchval'])>10:
        flash("filter must be 10 chars or less")
        session['searchval']=""
        session['state']=""
      elif len(session['searchval'])<1:
        flash("Enter something into the searchbox")
        session['state']=""
      else:
        flash('Filtering out every filename that does not contain "'+session['searchval']+'"')
        session['state']="search"
    elif ((request.args.get('home') != None and request.args.get('home') == 'blanco') and
          mode=="none"):
      mode="blanco"
      session['searchval'] = request.args.get('searchval')
      if len(session['searchval'])!=6 or not session['searchval'].isdigit():
        flash("Enter a 6 digit number")
        session['searchval']=""
        session['state']=""
      else:
        flash("holy shit, blanco mode")
        session['state']="blanco"
    #'guy' and 'folder' in same form, have to make sure we really want to change donor
    elif ((request.args.get('guy') != None and request.args.get('guy') != session['donor'])
        and mode == "none"):
      session['donor']=request.args.get('guy')
      mode="guy"
    elif request.args.get('folder') != None and mode == "none":
      session['current_folder']=request.args.get('folder')
      mode="folder"
    elif ((request.args.get('home') != None and request.args.get('home') == 'home') and
          mode=="none"):
      if 'donor' in session:
        del session['donor']
      if 'current_folder' in session:
        del session['current_folder']
      session['searchval']=""
      session['state']=""
      mode="home"
      
    #if search "state"
    if session['state']=="search":
      #the order stays intact in the Donator table, probably the only reason i'm grabbing it here
      guys=[]
      pull=Donator.query.with_entities(Donator.location)
      
      for eachpull in pull:
        match=False
        for root, dirs, files in os.walk(os.path.join(
          "static","sinks",eachpull.location), topdown=True):
          for val in files:
            if session['searchval'].lower() in val.lower() and cadchecker(val):
              guys.append(eachpull.location)
              match=True
              break
          if match == True:
            break
    #not search state, load everything
    else:
      #set all main folders
      guys=[]
      pull=Donator.query.with_entities(Donator.location)
      #this just converts whatever datatype SQL returns to strings
      #waste of time, probably something I don't know how to do right
      for eachpull in pull:
        guys.append(eachpull.location)
      
    #verify donor valid here, verify current_folder after folders[] loaded
    #session['donor'] not in guys should only happen if "hacked"
    if 'donor' not in session or session['donor'] not in guys:
      #initial load? set to silicatewastes
      if guys:
        session['donor']=guys[0]
      elif 'donor' in session:
        del session['donor']
    else:
      #setup select box.  screw javascript
      guys.remove(session['donor'])
      guys.insert(0,session['donor'])
    
    folders=[]
    if 'donor' in session:
      if session['state']=="search":
        #ok this works but there has to be a better way of doing this with deeper
        #understanding of os.walk
        for root, dirs, files in os.walk(os.path.join("static","sinks",session["donor"]),
                                         topdown=True):
          for val in dirs:
            match=False
            for root, dirs, files in os.walk(os.path.join("static","sinks",session["donor"],val),
                                         topdown=True):
              for val2 in files:
                if session['searchval'].lower() in val2.lower() and cadchecker(val2):
                  folders.append(val)
                  match=True
                  break
              if match==True:
                break;
          break
        folders=sorted(folders, key=str.casefold)
      else:
        for root, dirs, files in os.walk(os.path.join("static","sinks",session["donor"]),
                                         topdown=True):
          #set folders to all root folders in donor
          folders=sorted(dirs, key=str.casefold)
          break
    
      #verify current folder and set newpath
      if folders:
        if ('current_folder' not in session or session['current_folder'] not in folders or
            mode == "guy"):
          session['current_folder']=folders[0]
        else:
          #setup select box
          folders.remove(session['current_folder'])
          folders.insert(0,session['current_folder'])
        newpath=os.path.join("static","sinks",session['donor'],session['current_folder'])
      else:
        if 'current_folder' in session:
          del session['current_folder']
        newpath=os.path.join("static","sinks",session['donor'])
    
      #cads=[] moved this to top, has to exist
      for root, dirs, files in os.walk(newpath, topdown=True):
        for val in files:
          if cadchecker(val):
            if (not session['searchval'] or
                (session['state']=="search" and session['searchval'].lower() in val.lower())):
              newval=os.path.join(root,val)
              rated_sink = Sink.query.filter_by(location=newval[len("static/sinks/"):]).first()
              
              #need the +1 for last '/'.
              #just chopping of the directory info
              if 'current_folder' in session:
                newval=newval[len(os.path.join("static/sinks",session['donor'],
                                              session['current_folder']))+1:]
              else:
                newval=newval[len(os.path.join("static/sinks",session['donor']))+1:]
              
              newcad=(newval, rated_sink.id, rated_sink.avg_rating,
                      getratecolor(rated_sink.avg_rating))
              
              cads.append(newcad)

      #i only half understand this
      cads = sorted(cads, key=lambda tup: tup[0].lower())
    selectcolor=getselectcolor(session['state'])
    
    return render_template('silicate.html',title="silicatewastes", cads=cads, guys=guys,
                           folders=folders, searchval=session['searchval'], selectcolor=selectcolor,
                           state=session['state'])

######################################login#########################################################
######################################login#########################################################
######################################login#########################################################
######################################login#########################################################
######################################login#########################################################
######################################login#########################################################
######################################login#########################################################
######################################login#########################################################

@app.route('/login', methods=['POST', 'GET'])
def login():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
  
    user = User.query.filter_by(username=username).first()
      
    if user and check_pw_hash(password,user.hashpass):
      session['username'] = username
      return redirect('/')
    else:
      flash("login failed!")
    
  return render_template("login.html")

#########################################weaselwork###############################################
#########################################weaselwork###############################################
#########################################weaselwork###############################################
#########################################weaselwork###############################################
#########################################weaselwork###############################################
#########################################weaselwork###############################################
#########################################weaselwork###############################################
#########################################weaselwork###############################################
  
#make sure only dustyweasel can access this
@app.route('/weaselwork', methods=['GET','POST'])
def weaselwork():
  username=""
  if 'username' in session:
    username=session['username']
  
  if username!="dustyweasel":
    return redirect('/')
  
  message="no messages"
  adds=[]
  #initial display
  if request.method == 'GET':
    #this is actually a list of folders
    dxfs=[]
    for root, dirs, files in os.walk(os.path.join("static","sinks"), topdown=True):
      for val in dirs:
        dxfs.append(val)
      break
      
    return render_template('weasel.html',title="Weaselwork!", dxfs=dxfs, username=username)
  
  #clicked one of the buttons, do something
  elif request.method == 'POST':
    orders = request.form['orders']
    #can't ever have a folder name "death"
    if(orders=="death"):
      db.drop_all()
      db.create_all()
      message="Holy CRap!  You deleted f---ing everything!"
    elif(orders=="average"):
      #doing this the hacky way.  only hitting this button once.  who cares.
      #adding a average column to Sink a year after the fact
      #trash it or figure out sqlalchemy avg later.  probably click it once and trash it
      
      #from sqlalchemy.sql import func
      #      qry = session.query(func.max(Score.score).label("max_score"), 
      #              func.sum(Score.score).label("total_score"),
      #              )
      total = Sink.query.with_entities(Sink.id,Sink.location).order_by(Sink.id.desc()).first()[0]
      #return str(total)
      #average = Rating.query.filter_by(sink_id=1).all()
      #for ix in range(1,total+1):
      for ix in range(1,total+1):
        ratings = Rating.query.with_entities(Rating.stars, Rating.comment).filter_by(sink_id=ix)
        print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
        print(ix)
        totalval=0.0
        totalsum=0.0
        average=0.0
        for rating in ratings:
          print(rating.stars)
          totalval+=1
          totalsum+=rating.stars
        if(totalval!=0):
          average=totalsum/totalval
        print("average="+str(average))
        altersink = Sink.query.filter_by(id=ix).first()
        altersink.avg_rating=average
        db.session.add(altersink)
        print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
      db.session.commit()
    else:
      new_donor=Donator(orders)
      check = Donator.query.filter_by(location=orders).scalar()
      if not check:
        db.session.add(new_donor)
        db.session.commit()
      new_donor = Donator.query.filter_by(location=orders).first()
      
      for root, dirs, files in os.walk(os.path.join("static","sinks",orders),topdown=False):
        for val in files:
          #for every file anywhere in the orders directory if the sink
          #file isn't already in the sinks table stick it in
          if cadchecker(val):
          #if (val.lower().endswith('.dxf') or val.lower().endswith('.dwg') or
          #    val.lower().endswith('.ard') or val.lower().endswith('.asd')):
            
            check = Sink.query.filter_by(location=(os.path.join(root,val)[13:])).scalar()
            if not check:
              #adds isn't serious, it's just for display
              adds.append(os.path.join(root,val)[13:])
              new_sink=Sink(os.path.join(root,val)[13:],new_donor)
              
              db.session.add(new_sink)
            
      db.session.commit()
      
    #same as in get request, do it again after folder possibly added
    dxfs=[]
    for root, dirs, files in os.walk(os.path.join("static","sinks"), topdown=True):
      for val in dirs:
        dxfs.append(val)
      break
      
    return render_template('weasel.html',title="Weaselwork!", dxfs=dxfs, adds=adds,
                           message=message, username=username)
  
if __name__ == '__main__':
  app.run()

