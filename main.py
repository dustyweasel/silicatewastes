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
from sqlalchemy.sql import func

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
    self.avg_rating = None

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
    self.memberlevel=3 #standard user
    
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
#session['state']
#session['donor']
#session['current_folder']
#session['username']
#session['secret_pass']
#session['password']

#set donorval to "" to set back to silicatewastes
#set cloneguys to "" to clear it.  silly but whatever
#i think i can delete this riculousness now
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
#haven't used this, this time, maybe delete it
#maybe i'll need it again when i get the sink page running again
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

GLOBALRATEVAL=5
def getratecolor(val, seethrough):
  if val == None or val < 1.0:
    if seethrough=="yes":
      color = "transparent"
    else:
      color = "lightsteelblue"
  elif val >= 2.0:
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
    color="mediumaquamarine"
  else:
    color="red"
    
  return color

GLOBALSTATUSVAL=4
def getstatuscolor(val):
  if val==1:  #dictator
    color="sandybrown"
  elif val==0:  #hover
    color="aqua"
  elif val==2:  #donator
    color="lightgreen"
  elif val==3: #standard
    color="#66AACD"
  else: #oops
    color="red"
    
  return color
  
@app.before_request
def require_login():
  allowed_routes = ['index', 'login', 'register', 'stats', 'verify', 'stalk', 'demos']
  #need that '/static/' part for css i think
  if (request.endpoint not in allowed_routes and 'username' not in session and
    '/static/' not in request.path):
    
    flash("log in")
    
    #if 'username' in session:
    #  del session['username']
    if 'secret_pass' in session:
      del session['secret_pass']
    if 'password' in session:
      del session['password']
    
    return redirect('/')
  
##############################///////////////////////////########################################
##############################///////////////////////////########################################
##############################///////////////////////////########################################
##############################///////////////////////////########################################
##############################///////////////////////////########################################
##############################///////////////////////////########################################
##############################///////////////////////////########################################
##############################///////////////////////////########################################

#setting this up so any donor folder either has all files in main folder or in subfolders.  if
#any subfolders are detected that all files in donor folder are ignored

#i think this will crash if the file system doesn't exist or whatever.  
#i'm not checking for it yet.  who cares.
@app.route('/', methods=['GET'])
def index():
  #well if i ever need POST it's indented already
  if request.method == 'GET':
    cads=[]
    blancopackage=""
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
    if ((request.args.get('home') == None and session['state']=='stats') or
        (request.args.get('home') != None and request.args.get('home') == 'stats')):
      session['state']="stats"
      return redirect("/stats")
    elif request.args.get('home') != None and request.args.get('home') == 'search':
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
    elif session['state']=="blanco":
      guys=[]
      pull=Donator.query.with_entities(Donator.location)
      try:
        savesplit=""
        blancofile=open(os.path.join("static","blanco.txt"),'r')
        blancotemp=blancofile.read()
        blancosplit=blancotemp.split("break")
        for ix in range(len(blancosplit)):
          #check for blanco in any of those groups of 8
          if session['searchval'] in blancosplit[ix]:
            #found one
            savesplit=blancosplit[ix]
            break
          #if we found one
        if savesplit:
          if request.args.get('home') == 'blanco':
            flash("identical cutouts: "+savesplit)
          #global, create list of 16 including hyphens
          blancopackage=savesplit.strip('\n').split('\n')
          for ix in range(len(blancopackage)):
            blancopackage.append(blancopackage[ix][:3]+'-'+
                                            blancopackage[ix][3:])
        #no matches, just make a list of two, one with hyphen
        else:
          blancopackage=[]
          blancopackage.append(session['searchval'])
          blancopackage.append(session['searchval'][:3]+'-'+session['searchval'][3:])
          
          flash("No identical cutouts.  Searching only for "+blancopackage[0]+
                " and "+blancopackage[1])
      except Exception as e:
        flash(e)
        flash("something went wrong, email me if you want")
        session['searchval']=""
        session['state']=""
        
      for eachpull in pull:
        match=False
        for root, dirs, files in os.walk(os.path.join(
          "static","sinks",eachpull.location), topdown=True):
          for val in files:
            for ix in range(len(blancopackage)):
              if cadchecker(val) and blancopackage[ix] in val:
                guys.append(eachpull.location)
                match=True
                break
            if match == True:
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
      elif session['state']=="blanco":
        for root, dirs, files in os.walk(os.path.join("static","sinks",session["donor"]),
                                         topdown=True):
          for val in dirs:
            match=False
            for root, dirs, files in os.walk(os.path.join("static","sinks",session["donor"],val),
                                         topdown=True):
              for val2 in files:
                for ix in range(len(blancopackage)):
                  if cadchecker(val2) and blancopackage[ix] in val2:
                    folders.append(val)
                    match=True
                    break
                if match==True:
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
            blancomatch=False
            if session['state']=="blanco":
              for ix in range(len(blancopackage)):
                if blancopackage[ix] in val:
                  blancomatch=True
                  break
            
            if (session['state']=="" or
                (session['state']=="search" and session['searchval'].lower() in val.lower()) or
                (session['state']=="blanco" and blancomatch==True)):
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
                      getratecolor(rated_sink.avg_rating, "yes"))
              
              cads.append(newcad)

      #i only half understand this
      cads = sorted(cads, key=lambda tup: tup[0].lower())
    selectcolor=getselectcolor(session['state'])
    username=""
    if 'username' in session:
      username=session['username']
    
    return render_template('silicate.html',title="silicatewastes", cads=cads, guys=guys,
                           folders=folders, searchval=session['searchval'], selectcolor=selectcolor,
                           state=session['state'], blancopackage=blancopackage, username=username)

######################/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink###############
######################/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink###############
######################/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink###############
######################/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink###############
######################/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink###############
######################/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink###############
######################/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink###############
######################/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink###############

@app.route('/sink', methods=['GET','POST'])
def sink():
  #this is protected by /require_login
  #let it crash if they got here somehow
  #username=""
  #if 'username' in session:
  
  username=session['username']
  user = User.query.filter_by(username=username).first()
  colors=[]
  for ix in range(GLOBALSTATUSVAL):
    colors.append(getstatuscolor(ix))
  ratecolors=[]
  ratecolors.append(getratecolor(1.0,"no"))
  ratecolors.append(getratecolor(3.0,"no"))
  
  if request.method=='GET':
    #why bother checking if it's there, let it crash
    cad=request.args.get('cad')
    sink=Sink.query.filter_by(id=cad).first()
    ratecolor=getratecolor(sink.avg_rating,"no")
    user_rating = Rating.query.filter_by(user_id=user.id, sink_id=sink.id).first()
    ratings = Rating.query.filter(Rating.user_id != user.id, Rating.sink_id==sink.id).all()
  elif request.method=='POST':
    cad=request.form['cad']
    sink=Sink.query.filter_by(id=cad).first()
    rate=request.form['rate']
    if rate == "clear":
      #just delete it
      user_rating = Rating.query.filter_by(user_id=user.id, sink_id=sink.id).first()
      #if they're hitting the back button need to skip 2 statements
      if user_rating:
        db.session.delete(user_rating)
        db.session.commit()
      sink.avg_rating=(Rating.query.with_entities(func.avg(Rating.stars).label('average')).filter(
          Rating.sink_id==sink.id))
      #reload sink after commit()???
      db.session.commit()
      sink=Sink.query.filter_by(id=cad).first()
    else: #rate == "rate"
      legit=True
      #stars = request.form['stars']
      comment = request.form['comment']
      if len(comment)>60:
        flash("comment must be less than 60 chars")
        legit=False
      
      user_rating = Rating.query.filter_by(user_id=user.id, sink_id=sink.id).first()
      if user_rating:
        db.session.delete(user_rating)
        db.session.commit()
        sink.avg_rating=(Rating.query.with_entities(func.avg(Rating.stars).label('average')).filter(
          Rating.sink_id==sink.id))
        db.session.commit()
        flash("You people and your god damn back buttons.")
        flash("I hope you get a virus.")
        #flash("something has gone terribly wrong.  email me.")
        #legit=False
        
      if 'stars' not in request.form:
        flash("You have to pick a rating.")
        legit=False
        
      if legit == True:
        stars = request.form['stars']
        new_rating=Rating(stars,comment,user,sink)
        db.session.add(new_rating)
        db.session.commit()
        #i have no idea what .label is for or what it doesn't work without it.
        #what if i put something besides 'average'?
        sink.avg_rating=(Rating.query.with_entities(func.avg(Rating.stars).label('average')).filter(
          Rating.sink_id==sink.id))
        db.session.commit()
        
        sink=Sink.query.filter_by(id=cad).first()
    
    ratings = Rating.query.filter(Rating.user_id != user.id, Rating.sink_id==sink.id).all()
    ratecolor=getratecolor(sink.avg_rating,"no")
    user_rating = Rating.query.filter_by(user_id=user.id, sink_id=sink.id).first()
    
  return render_template("sink.html", sink=sink, username=username, ratecolor=ratecolor,
                         ratings=ratings, user_rating=user_rating, colors=colors, user=user,
                         ratecolors=ratecolors)

#######################/downloadfile/downloadfile/downloadfile###############################
#######################/downloadfile/downloadfile/downloadfile###############################
#######################/downloadfile/downloadfile/downloadfile###############################
#######################/downloadfile/downloadfile/downloadfile###############################
#######################/downloadfile/downloadfile/downloadfile###############################
#######################/downloadfile/downloadfile/downloadfile###############################
#######################/downloadfile/downloadfile/downloadfile###############################
#######################/downloadfile/downloadfile/downloadfile###############################

#apparently i shouldn't be doing this, supposed to use a proper web server
#instead of the flask server.  don't care for now plus maybe i don't get
#enough traffic for it to matter
@app.route("/downloadfile", methods=['POST'])
def downloadfile():
  if 'cancel' in request.form:
    return redirect("/")
  
  #this is protected by allowed_routes
  #if 'username' in session:
  username = session['username']
  user = User.query.filter_by(username=username).first()
    
  #let it crash
  cad = int(request.form['cad'])
  sink=Sink.query.filter_by(id=cad).first()
      
  try:
    sink.downloads+=1
    user.lastsink=sink.id
    #user downloads.  made that variabe for something else.  whatever.
    user.benefactor+=1
    db.session.commit()
    
    cadsplit = sink.location.split(os.path.sep)
    #should be same as donor / folder
    sinkdir=os.path.join(cadsplit[0],cadsplit[1])
    for ix in range(2,len(cadsplit)-1):
      sinkdir=os.path.join(sinkdir,cadsplit[ix])
    sinkname=cadsplit[len(cadsplit)-1]
    
    return send_from_directory(os.path.join("static","sinks",sinkdir),
                               sinkname, as_attachment=True)
  except Exception as e:
    flash("Something went terribly wrong.  Email me all this if you want:")
    flash(sink.location)
    flash(str(e))
    return redirect('/')

##########################/stats##################################################################
##########################/stats##################################################################
##########################/stats##################################################################
##########################/stats##################################################################
##########################/stats##################################################################
##########################/stats##################################################################
@app.route("/stats", methods=['GET'])
def stats():
  username=""
  if 'username' in session:
    username=session['username']
  
  if request.method=='GET':
    if request.args.get('screen') == None or request.args.get('screen') == 'stalk':
      return redirect('/stalk')
  else:
    return "whoops"

##########################stalk##################################################################
##########################stalk##################################################################
##########################stalk##################################################################
##########################stalk##################################################################
##########################stalk##################################################################
##########################stalk##################################################################
##########################stalk##################################################################
##########################stalk##################################################################
@app.route('/stalk', methods=['GET','POST'])
def stalk():
  username=""
  if 'username' in session:
    username=session['username']
    
  colors=[]
  for ix in range(GLOBALSTATUSVAL):
    colors.append(getstatuscolor(ix))

  if request.method == 'GET':
    if request.args.get('member') != None and 'username' in session:
      #if it's not an int, let it crash
      member = int(request.args.get('member'))
      memberdata=User.query.filter_by(id=member).first()
      #i have almost no memory of writing this beast
      # think it loads memberratings with Sink.location, id's?, Rating.stars, Rating.comment
      memberratings=(Sink.query.with_entities(Sink.location).join
                      (Rating, Rating.sink_id==Sink.id).filter_by
                      (user_id=memberdata.id).add_columns
                      (Rating.sink_id, Rating.stars, Rating.comment))
      #why doesn't the query set it to none if it finds no ratings?
      #oh well time for a hacky workaround
      try:
        print(memberratings[0].location)
      except Exception as e:
        memberratings=None
      return render_template("stalkmore.html", state=session['state'], screen="stalk",
                             memberdata=memberdata, memberratings=memberratings, username=username,
                             colors=colors)
    else:
      if request.args.get('member') != None:
        flash("log in")
      #gonna have to make this grab 100 at a time like sink if i ever get 1000's of users
      members=User.query.with_entities(User.id, User.username, User.catchphrase, User.memberlevel,
                                   User.benefactor, User.state, User.company).all()
   
  #this is just for messaging on the stalkmore page.  no one uses it
  elif request.method == 'POST':
    if 'username' not in session:
      #shouldn't be able to get here
      flash("log in.  not sure how you pulled this off.")
      return redirect('/')
    elif 'victim' in request.form:
      victim=int(request.form['victim'])
      victimemail=User.query.filter_by(id=victim).first()
      email=User.query.with_entities(User.email).filter_by(username=session['username']).first()
      harassment=session['username']
      harassment+="'s message: "
      if 'harassment' in request.form:
        harassment+=request.form['harassment']
      harassment+="\n\n"+session['username']+"'s email address: "+email.email
      harassment+=("\n\n Reply to "+session['username']+" at the email address above to establish "
      "contact.  If you don't want "+session['username']+" to know your email address then just "
      "delete this message.  If they're harassing you then email me at dustyweasel@protonmail.com "
      "and I'll silence them forever.")
      try:
        yag = yagmail.SMTP(os.getenv("EMAIL_USER"),os.getenv("EMAIL_PASS"))
        yag.send(victimemail.email, "message from "+session['username'], harassment)
        flash("Message sent to "+victimemail.username)
        return redirect('/stalk?member='+str(victimemail.id))
      except Exception as e:
        flash("Something went wrong.  Email me if you want:  dustyweasel@protonmail.com")
        return redirect('/')
    else:
      flash("Not sure what went wrong.  Email me if you want.")
      return redirect('/stalk')
  
  #should only be able to reach this on get request
  return render_template("stalk.html", state=session['state'], screen="stalk", members=members,
                         username=username, colors=colors)

######################################login / logout##############################################
######################################login / logout##############################################
######################################login / logout##############################################
######################################login / logout##############################################
######################################login / logout##############################################
######################################login / logout##############################################
######################################login / logout##############################################
######################################login / logout##############################################

@app.route('/login', methods=['POST', 'GET'])
def login():
  if 'username' in session:
    del session['username']
  if 'secret_pass' in session:
    del session['secret_pass']
  if 'password' in session:
    del session['password']
  username=""
    
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
  
    user = User.query.filter_by(username=username).first()
      
    if user and check_pw_hash(password,user.hashpass):
      session['username'] = username
      return redirect('/')
    else:
      flash("login failed!")
      
  #just pass username in places like this to make sure you logged them out
  return render_template("login.html", username=username)

@app.route('/logout')
def logout():
  if 'username' in session:
    del session['username']
  if 'secret_pass' in session:
    del session['secret_pass']
  if 'password' in session:
    del session['password']
  return redirect('/')

###############################################register########################################
###############################################register########################################
###############################################register########################################
###############################################register########################################
###############################################register########################################
###############################################register########################################
###############################################register########################################
###############################################register########################################

@app.route('/register', methods=['POST', 'GET'])
def register():
  #for hackers only (or back button?)
  if 'username' in session:
    del session['username']
  if 'password' in session:
    del session['password']
  if 'secret_pass' in session:
    del session['secret_pass']
    #flash("Don't hit refresh on that screen.  Start over.")
    return redirect('/')
      
  if request.method == 'GET':
    username=""
    newusername=""
    password=""
    verify=""
    email=""
    company=""
    catchphrase=""
  
  elif request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    verify = request.form['verify']
    email = request.form['email']
    company = request.form['companyname']
    catchphrase = request.form['catchphrase']
    usstate = request.form['state']
    if 'dust' not in request.form:
      crybaby=3
    else:
      crybaby = request.form['dust']
      if crybaby=="True":
        crybaby=1
      elif crybaby=="False":
        crybaby=0
      
    allset=True
    #validate
    if len(username)<1 or len(username)>20:
      flash("username must be 1-20 characters")
      allset=False
    
    user_exists = User.query.filter_by(username=username).first()
    if user_exists:
      flash("username already taken!")
      allset=False
      
    if len(password)<1 or len(password)>30:
      flash("password must be 1-30 characters")
      allset=False
      
    if password!=verify:
      flash("passwords don't match!")
      allset=False
      
    user_exists = User.query.filter_by(email=email).first()
    if user_exists:
      flash("email already taken!")
      allset=False
      
    if len(email)>60:
      flash("no emails longer than 60 characters")
      allset=False
    elif len(email)<1:
      flash("enter an email address")
      allset=False
      
    if len(company)>60:
      flash("no company names longer than 60 characters")
      allset=False
      
    if len(catchphrase)>60:
      flash("no catchphrases longer than 60 characters")
      allset=False
      
    if len(usstate)>2:
      flash("no states longer than 2 characters.  not sure how you pulled that off.")
      allset=False
      
    if allset:
      new_user = User(username,"",email,company,catchphrase,usstate,crybaby)
      session['secret_pass']=id_generator()
      
      try:
        yag = yagmail.SMTP(os.getenv("EMAIL_USER"),os.getenv("EMAIL_PASS"))
        yag.send(email, "verify thyself", session['secret_pass'])
      except Exception as e:
        #why won't this work here?
        #flash(e)
        flash("Maybe something's wrong with the email address you entered?  Start over.")
        flash("You entered: "+email)
        #session['secret_pass']=""
        return redirect('/')
        
      session['tempname']=username
      session['password']=password
      session['email']=email
      session['company']=company
      session['catchphrase']=catchphrase
      session['usstate']=usstate
      session['crybaby']=str(crybaby)
      
      flash("YOU ENTERED: "+email)
      return render_template("verify.html", user=new_user)
    else:
      newusername=username
      username=""
      if 'username' in session:
        del session['username']
      if 'secret_pass' in session:
        del session['secret_pass']
      if 'password' in session:
        del session['password']
  
  return render_template("register.html", newusername=newusername, username=username,
                         email=email, company=company, catchphrase=catchphrase)

####################################verify######################################################
####################################verify######################################################
####################################verify######################################################
####################################verify######################################################
####################################verify######################################################
####################################verify######################################################
####################################verify######################################################
####################################verify######################################################

@app.route('/verify', methods=['POST'])
def verify():
  if 'secret_pass' not in session:
    if 'username' in session:
      del session['username']
    #if 'secret_pass' in session:
    #del session['secret_pass']
    if 'password' in session:
      del session['password']
    flash("No, seriously.  Start over.  Go back to the register page.")
    
    return redirect('/')
    
  #probably should verify again here, hackers don't need my form
  #...wait this is a huge hole, isn't it?  store a copy in the session and compare?
  username = request.form['username']
  #password = request.form['password']
  email = request.form['email']
  company = request.form['company']
  catchphrase = request.form['catchphrase']
  usstate = request.form['state']
  secretpass = request.form['secretpass']
  #if 'dust' not in request.form:
  #  dust=3
  #else:
  dust = request.form['dust']
    
  #new_user = User(username, session['password'], email, company, catchphrase, usstate, dust)
  #del session['password']
  
  if secretpass == session['secret_pass']:
    if (username==session['tempname'] and email==session['email'] and company==session['company']
        and catchphrase==session['catchphrase'] and usstate==session['usstate'] and
        dust==session['crybaby']):
      new_user = User(username, session['password'], email, company, catchphrase, usstate, dust)
      flash("Welcome to the silicate wastes, "+username+".")
      db.session.add(new_user)
      db.session.commit()
      session['username'] = new_user.username
    else:
      flash("Not sure how you did that haxOr")
  else:
    flash("Wrong secret key.  Start over.")
    
  #if 'username' in session:
  #  del session['username']
  if 'secret_pass' in session:
    del session['secret_pass']
  if 'password' in session:
    del session['password']
  if 'tempname' in session:
    del session['tempname']
  if 'email' in session:
    del session['email']
  if 'companyname' in session:
    del session['companyname']
  if 'catchphrase' in session:
    del session['catchphrase']
  if 'usstate' in session:
    del session['usstate']
  if 'crybaby' in session:
    del session['crybaby']
    
  return redirect('/')

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
        if average != None:
          altersink.avg_rating=average
        else:
          altersink.avg_rating= None
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

