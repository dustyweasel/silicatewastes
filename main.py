#ALTER TABLE sink
#ADD avg_rating float; 
#also user avg_rating
#also user sum_ruting? nah, not yet

from flask import Flask, request, redirect, url_for, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask import send_from_directory
import os
import yagmail
import string
import random
from hashutils import make_pw_hash, check_pw_hash
from sqlalchemy.sql import func

#you just set track mods, debus, and echo to False.  ran it forever without that.
#see if it makes any difference
app = Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")

app.config['SQLALCHEMY_ECHO'] = False

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
  avg_rating = db.Column(db.Float)
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
    self.avg_rating = None
    
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

#set donor / folder based on cad id
def sinksplit(sinkid):
  entry = Sink.query.filter_by(id=sinkid).first()
  
  try:
    cad = entry.location
  except Exception as e:
    flash("Can't find sink.  Stop messing with the URL.")
    session['donor']=""
    session['current_folder']=""
    return redirect(url_for('index'))
  
  cadsplit = cad.split(os.path.sep)
  skip=False
  
  session['donor']=cadsplit[0]
  
  #if no base folders
  for root, dirs, files in os.walk(os.path.join("static","sinks",cadsplit[0]), topdown=True):
    if len(dirs) == 0:
      skip=True
    break
  
  if not skip:
    session['current_folder']=cadsplit[1]
  else:
    session['current_folder']=""

GLOBALRATEVAL=4
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
  else:
    color = "yellow" #oops
    
  return color

#i think this is just for coloring selectboxes based on state
def getselectcolor(val):
  if val==chr(0):
    color="#f4f4f0"
  elif val==chr(1):
    color="lightblue"
  elif val==chr(2):
    color="mediumaquamarine"
  else:
    color="red" #oops
    
  return color

GLOBALSTATUSVAL=4 #4 choices
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

#just stuck this in a function in case i ever add another substate
#then only have to fix one spot instead of 100
def setstate(which,val):
  if which=="reset":
    session['state']=chr(0)+chr(0)
  elif which=="main":
    session['state']=val+session['state'][1:]
  elif which=="substate":
    session['state']=session['state'][:1]+val


#wtf
#127.0.0.1 - - [09/Apr/2020 05:11:06] "GET /favicon.ico HTTP/1.1" 302 -

@app.before_request
def require_login():
  allowed_routes = ['index', 'login', 'register', 'stats', 'verify', 'stalk', 'demos', 'dust',
                    'statsinks', 'raters', 'recent', 'errata', 'stateswitch']
  #need that '/static/' part for css i think
  if (request.endpoint not in allowed_routes and 'username' not in session and
    '/static/' not in request.path):
    
    flash("log in")
    
    if 'secret_pass' in session:
      del session['secret_pass']
    if 'password' in session:
      del session['password']
    
    #if they get blocked but they're in stats, search, or blanco then let them stay on current
    #screen instead of resetting
    if 'state' in session and (ord(session['state'][:1])!=4 and ord(session['state'][:1])!=1 and
                               ord(session['state'][:1])!=2):
      del session['state']
    
    return redirect(url_for('index'))
  
##############################///////////////////////////########################################
##############################///////////////////////////########################################
##############################///////////////////////////########################################
##############################///////////////////////////########################################
##############################///////////////////////////########################################
##############################///////////////////////////########################################
##############################///////////////////////////########################################
##############################///////////////////////////########################################

#setting this up so any donor folder either has all files in main folder or in subfolders.  if
#any subfolders are detected then all files in donor folder are ignored

#only states None,0,1,2 should get here
@app.route('/', methods=['GET'])
def index():
  #well if i ever need POST it's indented already
  if request.method == 'GET':
    if request.args.get('cad')!=None:
      #set donor / foder based on cad id
      #(this is actually the only place this function is called these days)
      sinksplit(request.args.get('cad'))
      setstate("reset",None)
    
    if 'searchval' not in session:
      session['searchval']=""
    if 'state' not in session:
      #session['state']=chr(0)+chr(0)
      setstate("reset", None)
    if 'page' not in session:
      session['page']=0
    
    if ord(session['state'][:1])==3:
      return redirect(url_for('chat'))
    if ord(session['state'][:1])==4:
      return redirect(url_for('stats'))
    
    cads=[]
    blancopackage=""
    
    #session['state']
    #byte 0 = main state
    #0 = home
    #1 = search
    #2 = blanco
    #3 = chat
    #4 = stats
    
    #byte 1 = screen (stats)
    #0 = sinks
    #1 = raters
    #2 = stalk
    #3 = dust
    #4 = recent
    
    #i think they meant integer
    #Return the iteger that represents the character "h":
    #x = ord("h")
    
    #chr() is what you're looking for:
    #print chr(65) # will print "A"
    
    mode=""
    if request.args.get('guy') != None and request.args.get('guy') != session['donor']:
      session['donor']=request.args.get('guy')
      mode="guy"
    elif request.args.get('folder') != None:
      session['current_folder']=request.args.get('folder')
      #mode="folder"
        
###################### state switch block ############################################
###################### state switch block ############################################

###########if state = default########################################################
    if ord(session['state'][:1])==0:
   
#set guys / selected donor   
      #guys = root folders based on database, not file structure
      #(should be the same thing)
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

#set folders      
      folders=[]
      if 'donor' in session: #rest state stuff within this if statement
        for root, dirs, files in os.walk(os.path.join("static","sinks",session["donor"]),
                                          topdown=True):
          #set folders to all root folders in donor
          folders=sorted(dirs, key=str.casefold)
          break
        
#set current_folder / newpath
        if folders:
          if ('current_folder' not in session or session['current_folder'] not in folders or
              mode == "guy"):
            session['current_folder']=folders[0]
              
          newpath=os.path.join("static","sinks",session['donor'],session['current_folder'])
        else:
          if 'current_folder' in session:
            del session['current_folder']
          newpath=os.path.join("static","sinks",session['donor'])

#load files        
        #cads=[] moved this to top, has to exist
        for root, dirs, files in os.walk(newpath, topdown=True):
          for val in files:
            if cadchecker(val):
                
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
        
##############if state=="search": ######################################################
    elif ord(session['state'][:1])==1:
      
#set guys / selected donor
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
      if 'donor' not in session or session['donor'] not in guys:
        #initial load? set to silicatewastes
        if guys:
          session['donor']=guys[0]
        elif 'donor' in session:
          del session['donor']

#set folders
      folders=[]
      if 'donor' in session:
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

#set current_folder / newpath
#(this part is the same for all 3 states.  that's why /index used to be monolithic with state
#checks here and there but it was nasty to read.  now there's one state check.

        if folders:
          if ('current_folder' not in session or session['current_folder'] not in folders or
              mode == "guy"):
            session['current_folder']=folders[0]
              
          newpath=os.path.join("static","sinks",session['donor'],session['current_folder'])
        else:
          if 'current_folder' in session:
            del session['current_folder']
          newpath=os.path.join("static","sinks",session['donor'])
          
#load files
        #cads=[] moved this to top, has to exist
        for root, dirs, files in os.walk(newpath, topdown=True):
          for val in files:
            if cadchecker(val):
      
              if session['searchval'].lower() in val.lower():
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
            
######if session['state']=="blanco" ########################################################
    elif ord(session['state'][:1])==2:
      
#set guys / selected donor 
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
          #create list of 16 including hyphens
          blancopackage=savesplit.strip('\n').split('\n')
          for ix in range(len(blancopackage)):
            blancopackage.append(blancopackage[ix][:3]+'-'+
                                            blancopackage[ix][3:])
        #no matches, just make a list of two, one with hyphen
        else:
          blancopackage=[]
          blancopackage.append(session['searchval'])
          blancopackage.append(session['searchval'][:3]+'-'+session['searchval'][3:])
          
      except Exception as e:
        flash(e)
        flash("something went wrong, email me if you want")
        session['searchval']=""
        setstate("reset",None)
        
      #probably should collect files first and THEN collect folders, who
      #cares for now
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
        
      if 'donor' not in session or session['donor'] not in guys:
        #initial load? set to silicatewastes
        if guys:
          session['donor']=guys[0]
        elif 'donor' in session:
          del session['donor']

#set folders
      folders=[]
      if 'donor' in session:
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

#set current_folder / newpath
        if folders:
          if ('current_folder' not in session or session['current_folder'] not in folders or
              mode == "guy"):
            session['current_folder']=folders[0]
              
          newpath=os.path.join("static","sinks",session['donor'],session['current_folder'])
        else:
          if 'current_folder' in session:
            del session['current_folder']
          newpath=os.path.join("static","sinks",session['donor'])
          
#load files
        #cads=[] moved this to top, has to exist
        for root, dirs, files in os.walk(newpath, topdown=True):
          for val in files:
            if cadchecker(val):
              blancomatch=False
              for ix in range(len(blancopackage)):
                if blancopackage[ix] in val:
                  blancomatch=True
                  break
                
              if blancomatch==True:
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
      
    else:
      return "index failure "+str(ord(session['state'][:1]))
    
##################### end of state switch block #####################################################
##################### end of state switch block #####################################################
    
    #i only half understand this
    cads = sorted(cads, key=lambda tup: tup[0].lower())
    selectcolor=getselectcolor(session['state'][:1])
    username=""
    if 'username' in session:
      username=session['username']
    
    selectdonor=""
    selectfolder=""
    if 'donor' in session:
      selectdonor=session['donor']
    if 'current_folder' in session:
      selectfolder=session['current_folder']
      
    return render_template('silicate.html',title="silicatewastes", cads=cads, guys=guys,
                           folders=folders, searchval=session['searchval'], selectcolor=selectcolor,
                           state=ord(session['state'][:1]), blancopackage=blancopackage,
                           username=username,
                           selectdonor=selectdonor, selectfolder=selectfolder)

######################/stateswitch/stateswitch/stateswitch#############################################
######################/stateswitch/stateswitch/stateswitch#############################################
######################/stateswitch/stateswitch/stateswitch#############################################
######################/stateswitch/stateswitch/stateswitch#############################################
######################/stateswitch/stateswitch/stateswitch#############################################
######################/stateswitch/stateswitch/stateswitch#############################################
######################/stateswitch/stateswitch/stateswitch#############################################
######################/stateswitch/stateswitch/stateswitch#############################################

@app.route('/stateswitch', methods=['GET'])
def stateswitch():
  #only way to get here supposed to be base html's menu buttons
  #let it crash otherwise
  home = int(request.args.get('home'))
  
  #0 trying to get back to default state, let them
  if home==0:
    if 'donor' in session:
      del session['donor']
    if 'current_folder' in session:
      del session['current_folder']
    session['searchval']=""
    setstate("reset",None)
    return redirect(url_for('index'))
          
  #1 trying to get to search state
  elif home==1:
    #need to make sure if 'home' == 'search' then form sends back 'searchval' too
    #i'll let it crash
    #session['searchval'] = request.args.get('searchval')
    if len(request.args.get('searchval'))>10: #hackers only
      flash("filter must be 10 chars or less")
      session['searchval']=""
    elif len(request.args.get('searchval'))<1:
      #just stuffed next 6 lines in without thinking about it, didn't take time
      #relearn code
      if 'searchval' not in session or session['searchval']=="":
        flash("Enter something into the searchbox")
      else:
        session['searchval']=""
        setstate("reset",None)
        return redirect(url_for('index'))
      #setstate("reset", None)
    else:
      session['searchval'] = request.args.get('searchval')
      flash('Filtering out every filename that does not contain "'+session['searchval']+'"')
      setstate("main", chr(1))
    return redirect(url_for('index'))
          
  #2 trying to get to blanco state
  elif home==2:
    #session['searchval'] = request.args.get('searchval')
    if len(request.args.get('searchval'))!=6 or not request.args.get('searchval').isdigit():
      flash("Enter a 6 digit number")
    else:
      session['searchval'] = request.args.get('searchval')
      setstate("main",chr(2))
    return redirect(url_for('index'))
            
  #3 trying to get to news state
  elif home==3:
    if 'username' in session:
      setstate("main",chr(3))
      return redirect(url_for('chat'))
    else:
      flash("log in")
      return redirect(url_for('index'))
      
  #4 trying to get to stats state
  elif int(request.args.get('home'))==4:
    setstate("main",chr(4))
    return redirect(url_for('stats'))
  
  else:
    return "something went terribly wrong / stateswitch"

######################/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink###############
######################/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink###############
######################/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink###############
######################/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink###############
######################/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink###############
######################/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink###############
######################/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink###############
######################/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink/sink###############

@app.route('/sink', methods=['GET'])
def sink():
  #this is protected by /require_login
  #let it crash if they got here somehow
  
  username=session['username']
  user = User.query.filter_by(username=username).first()
  #why bother checking if it's there, let it crash
  cad=int(request.args.get('cad'))
  if user.lastsink!=0 and user.lastsink != cad:
    previous_rating = Rating.query.filter_by(user_id=user.id, sink_id=user.lastsink).first()
    if previous_rating==None:
      return redirect(url_for('previous_sink', cad=cad, pre_cad=user.lastsink))
  
  #colors, ratecolors, and ratecolor, oh my
  colors=[]
  for ix in range(GLOBALSTATUSVAL):
    colors.append(getstatuscolor(ix))
  ratecolors=[]
  for ix in range(1,GLOBALRATEVAL):
    ratecolors.append(getratecolor(float(ix),"no"))
    
  sink=Sink.query.filter_by(id=cad).first()
  ratecolor=getratecolor(sink.avg_rating,"no")
  user_rating = Rating.query.filter_by(user_id=user.id, sink_id=sink.id).first()
  ratings = Rating.query.filter(Rating.user_id != user.id, Rating.sink_id==sink.id).all()
  
  return render_template("sink.html", sink=sink, username=username, ratecolor=ratecolor,
                         ratings=ratings, user_rating=user_rating, colors=colors, user=user,
                         ratecolors=ratecolors, state=ord(session['state'][:1]))

######################/previous_sink########################################################
######################/previous_sink########################################################
######################/previous_sink########################################################
######################/previous_sink########################################################
######################/previous_sink########################################################
######################/previous_sink########################################################
######################/previous_sink########################################################
######################/previous_sink########################################################
@app.route('/previous_sink', methods=['GET'])
def previous_sink():
  #if this stuff isn't here let it crash
  username=session['username']
  user = User.query.filter_by(username=username).first()
  cad=request.args.get('cad')
  pre_cad=request.args.get('pre_cad')
  
  sink=Sink.query.filter_by(id=cad).first()
  previous_sink=Sink.query.filter_by(id=pre_cad).first()
  if previous_sink == None:
    user.lastsink=0
    db.session.commit()
    return redirect(url_for('sink', cad=cad))
  
  ratecolors=[]
  for ix in range(1,GLOBALRATEVAL):
    ratecolors.append(getratecolor(float(ix),"no"))
  
  return render_template("previous_sink.html", sink=sink, previous_sink=previous_sink,
                         ratecolors=ratecolors, username=username)

#send it 2 sink id's.  one to rate and one to send to after rate.  could be the same.
@app.route('/rate_sink', methods=['POST'])
def rate_sink():
  username=session['username']
  user = User.query.filter_by(username=username).first()
  
  cad=request.form['cad']
  sink=Sink.query.filter_by(id=cad).first()
  goal=request.form['goal']
  rate=request.form['rate']
  if rate == "clear":
    #just delete it
    user_rating = Rating.query.filter_by(user_id=user.id, sink_id=sink.id).first()
    #if they're hitting the back button need to skip 2 statements
    if user_rating:
      db.session.delete(user_rating)
      db.session.commit()
      user.avg_rating=func.round((Rating.query.with_entities(
        func.avg(Rating.stars).label('average')).filter(Rating.user_id==user.id)),2)
      sink.avg_rating=func.round((Rating.query.with_entities(
        func.avg(Rating.stars).label('average')).filter(Rating.sink_id==sink.id)),2)
      db.session.commit()
  elif rate == "later":
    user.lastsink=0
    db.session.commit()
  else: #rate == "rate"
    legit=True
    
    #probably should setup database to have unique sink.id/user.id in Ratings
    #(can you do that?)
    #instead of relying on python to take care of it.  keep an eye out for double ratings
    user_rating = Rating.query.filter_by(user_id=user.id, sink_id=sink.id).first()
    if user_rating:
      db.session.delete(user_rating)
      db.session.commit()
      sink.avg_rating=func.round((Rating.query.with_entities(
        func.avg(Rating.stars).label('average')).filter(Rating.sink_id==sink.id)),2)
      db.session.commit()
      flash("You people and your god damn back buttons.")
      flash("I hope you get a virus.")
      
    comment = request.form['comment']
    if len(comment)>60:
      flash("comment must be less than 60 chars")
      legit=False
        
    if 'stars' not in request.form:
      flash("You have to pick a rating.")
      legit=False
        
    if legit == True:
      stars = request.form['stars']
      new_rating=Rating(stars,comment,user,sink)
      db.session.add(new_rating)
      db.session.commit()
      if int(stars) == 1:
        flash("Hey if this drawing sucked why don't you send me a good one?")
        flash("dustyweasel@protonmail.com")
      user.avg_rating=func.round((Rating.query.with_entities(
        func.avg(Rating.stars).label('average')).filter(Rating.user_id==user.id)),2)
      #i have no idea what .label is for or why it doesn't work without it.
      #what if i put something besides 'average'?
      sink.avg_rating=func.round((Rating.query.with_entities(
        func.avg(Rating.stars).label('average')).filter(Rating.sink_id==sink.id)),2)
      db.session.commit()
        
      #sink=Sink.query.filter_by(id=cad).first()
  
  return redirect(url_for('sink', cad=goal))

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
    #screen=""
    #if 'screen' in request.form:
    #  screen = request.form['screen']
    #page=0
    #if 'page' in request.form:
    #  page = request.form['page']
    return redirect('/')
  #return redirect(url_for('previous_sink', cad=cad, pre_cad=user.lastsink)) 
  
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
    #flash(len(cadsplit))
    #should be same as donor / folder
    if len(cadsplit) != 2:
      sinkdir=os.path.join(cadsplit[0],cadsplit[1])
    else:
      sinkdir=os.path.join(cadsplit[0])
    #flash(sinkdir)
    for ix in range(2,len(cadsplit)-1):
      sinkdir=os.path.join(sinkdir,cadsplit[ix])
    sinkname=cadsplit[len(cadsplit)-1]
    
    #flash(sinkdir)
    #flash(sinkname)
    #return redirect('/')
    
    return send_from_directory(os.path.join("static","sinks",sinkdir),
                               sinkname, as_attachment=True)
  except Exception as e:
    flash("Something went terribly wrong.  Email me all this if you want:")
    flash(sink.location)
    flash(str(e))
    return redirect('/')

##########################/chat##################################################################
##########################/chat##################################################################
##########################/chat##################################################################
##########################/chat##################################################################
##########################/chat##################################################################
##########################/chat##################################################################
##########################/chat##################################################################
##########################/chat##################################################################

@app.route('/chat', methods=['GET','POST'])
def chat():
  username=session['username']
  
  if request.method == 'POST':
    if 'babble' in request.form:
      babble = request.form['babble']
      if len(babble)>60 or len(babble)<2:
        flash("babblings must be 2-60 chars")
      else:
        ref_user = user = User.query.filter_by(username=username).first()
        new_babble = Babblings(babble, ref_user)
          
        db.session.add(new_babble)
        db.session.commit()
  
  prebabblings = Babblings.query.order_by(Babblings.id.desc()).all()
  babblings=[]
  #better to do this in jinja?  who cares
  for ix in range(len(prebabblings)):
    if ix%2 == 0:
      babblings.append(("linen", prebabblings[ix]))
    else:
      babblings.append(("wheat", prebabblings[ix]))
    
  colors=[]
  for ix in range(GLOBALSTATUSVAL):
    colors.append(getstatuscolor(ix))
  
  return render_template("chat.html", babblings=babblings, username=username,
                         state=ord(session['state'][:1]), colors=colors,
                         searchval=session['searchval'])

##########################errata##############################################################
##########################errata##############################################################
##########################errata##############################################################
##########################errata##############################################################
##########################errata##############################################################
##########################errata##############################################################
##########################errata##############################################################
##########################errata##############################################################

@app.route('/errata', methods=['GET'])
def errata():
  #username=""
  #if 'username' in session:
  username=session['username']
  
  return render_template("errata.html", username=username, state=session['state'][:1])

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
  
  if request.args.get('screen')!=None:
    #session['state']=session['state'][:1]+chr(int(request.args.get('screen')))
    setstate("substate", chr(int(request.args.get('screen'))))
  
  #if request.method=='GET':
  #if (request.args.get('screen') == None or request.args.get('screen') == "" or
  #    request.args.get('screen') == 'statsinks'):
  #  page=""
  cycle=""
  if ord(session['state'][1:2])==0:
    #if request.args.get('page') != None:
    #  page = request.args.get('page')
    if request.args.get('cycle') != None:
      cycle = request.args.get('cycle')
     #return redirect(url_for('previous_sink', cad=cad, pre_cad=user.lastsink)) 
    #return redirect(url_for('statsinks', page=page, cycle=cycle))
    return redirect(url_for('statsinks', cycle=cycle))
  #elif request.args.get('screen') == 'stalk':
  elif ord(session['state'][1:2])==2:
    return redirect('/stalk')
  #elif request.args.get('screen') == 'raters':
  elif ord(session['state'][1:2])==1:
    return redirect('/raters')
  #elif request.args.get('screen') == 'recent':
  elif ord(session['state'][1:2])==4:
    return redirect('/recent')
  #elif request.args.get('screen') == 'dust':
  elif ord(session['state'][1:2])==3:
    return redirect('/dust')
  else:
    return ("i don't know what just happened.  email me and we'll talk about it"
      +str(ord(session['state'][:1])))

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
      return render_template("stalkmore.html", state=ord(session['state'][:1]),
                             screen=ord(session['state'][1:2]),
                             memberdata=memberdata, memberratings=memberratings, username=username,
                             colors=colors, searchval=session['searchval'])
    else:
      if request.args.get('member') != None:
        flash("log in")
        #screen=""
        #if request.args.get('screen') != None:
        #  screen = request.args.get('screen')
        return redirect('index')
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
  return render_template("stalk.html", state=ord(session['state'][:1]),
                         screen=ord(session['state'][1:2]),
                         members=members,
                         username=username, colors=colors, searchval=session['searchval'])


####################################statsinks###################################################
####################################statsinks###################################################
####################################statsinks###################################################
####################################statsinks###################################################
####################################statsinks###################################################
####################################statsinks###################################################
####################################statsinks###################################################
####################################statsinks###################################################

@app.route('/statsinks', methods=['GET'])
def statsinks():
  username=""
  if 'username' in session:
    username=session['username']
  #if request.args.get('page') == None or request.args.get('page') == "":
  #  page=0
  #else:
  #  page=int(request.args.get('page'))
  if request.args.get('cycle') != None:
    cycle=request.args.get('cycle')
    if cycle == "previous" and session['page'] > 0:
      session['page']-=1
    elif cycle == "next":
      session['page']+=1
  
  topdownloads=(Sink.query.with_entities(Sink.downloads, Sink.location, Sink.id,Sink.avg_rating)
                .order_by(Sink.downloads.desc()).order_by(Sink.id).limit(100).offset(
                  100*session['page']))

  totaldownloads=User.query.with_entities(func.sum(User.benefactor).label('total')).all()[0][0]
  
  supertopdownloads=[]
  ix=1+(100*session['page'])
  for download in topdownloads:
    supertopdownloads.append((ix,download.location, download.downloads,download.avg_rating,
                             download.id,getratecolor(download.avg_rating,"yes")))
    ix+=1
  
  return render_template("stats.html", state=ord(session['state'][:1]),
                         screen=ord(session['state'][1:2]),
                         topdownloads=supertopdownloads, totaldownloads=totaldownloads,
                         arrows="yes", page=session['page'], username=username,
                         searchval=session['searchval'])

#######################################raters###############################################
#######################################raters###############################################
#######################################raters###############################################
#######################################raters###############################################
#######################################raters###############################################
#######################################raters###############################################
#######################################raters###############################################
#######################################raters###############################################

@app.route('/raters', methods=['GET'])
def raters():
  username=""
  if 'username' in session:
    username=session['username']
  colors=[]
  for ix in range(GLOBALSTATUSVAL):
    colors.append(getstatuscolor(ix))
  
  #i could do all this with one line of sqlalchemy if i knew what i was doing, a lot of places
  #like that in /stats.  don't need all these damn tuples and for loops and sorts
  raters=User.query.with_entities(User.id, User.username, User.memberlevel, User.benefactor,
                                  User.avg_rating)
  
  #still probably a faster way to do this
  totalrates=Rating.query.with_entities(func.count(Rating.id)).first()[0]
  
  superraters=[]
  for rater in raters:
    superraters.append((rater.id, rater.username, rater.memberlevel, rater.benefactor,
                       rater.avg_rating, Rating.query.with_entities(
                         func.count(Rating.user_id)).filter_by(user_id=rater.id).first()[0]))
                       
  superraters = sorted(superraters, key=lambda tup: (tup[0]))
  superraters = sorted(superraters, key=lambda tup: (tup[5]), reverse = True)
  
  
  return render_template("raters.html", state=ord(session['state'][:1]),
                         screen=ord(session['state'][1:2]),
                         superraters=superraters, colors=colors, username=username,
                         totalrates=totalrates, searchval=session['searchval'])

##########################################recent#############################################
##########################################recent#############################################
##########################################recent#############################################
##########################################recent#############################################
##########################################recent#############################################
##########################################recent#############################################
##########################################recent#############################################
##########################################recent#############################################

@app.route('/recent', methods=['GET'])
def recent():
  username=""
  if 'username' in session:
    username=session['username']
  
  colors=[]
  for ix in range(GLOBALSTATUSVAL):
    colors.append(getstatuscolor(ix))
  
  ratings=Rating.query.with_entities(Rating.user_id, Rating.sink_id, Rating.stars,
                                           Rating.comment).order_by(Rating.id.desc()).limit(100)
  
  #again i bet i could do all this with sqlalchemy
  superratings=[]
  for rating in ratings:
    location=Sink.query.with_entities(Sink.location).filter_by(id=rating.sink_id).first()[0]
    name=User.query.with_entities(User.username).filter_by(id=rating.user_id).first()[0]
    memberlevel=User.query.with_entities(User.memberlevel).filter_by(id=rating.user_id).first()[0]
    average=Sink.query.with_entities(Sink.avg_rating).filter_by(id=rating.sink_id).first()[0]
    
    superratings.append((location,name,rating.stars,rating.comment,memberlevel,
                               rating.user_id,rating.sink_id,average,getratecolor(average,"no")))
    
  return render_template("recent.html", state=ord(session['state'][:1]),
                         screen=ord(session['state'][1:2]),
                         ratings=superratings, colors=colors, username=username,
                         searchval=session['searchval'])

#######################################dust#################################################
#######################################dust#################################################
#######################################dust#################################################
#######################################dust#################################################
#######################################dust#################################################
#######################################dust#################################################
#######################################dust#################################################
#######################################dust#################################################

@app.route('/dust', methods=['GET'])
def dust():
  #dusters=User.query.with_entities(User.dustmask).all()
  #total = Sink.query.with_entities(func.count(Sink.id)).first()[0]
  yes = User.query.with_entities(func.count(User.dustmask)).filter_by(dustmask=1).first()[0]
  no = User.query.with_entities(func.count(User.dustmask)).filter_by(dustmask=0).first()[0]
  abstain = User.query.with_entities(func.count(User.dustmask)).filter_by(dustmask=3).first()[0]
  
  username=""
  if 'username' in session:
    username=session['username']
  
  # don't think we need page anymore
  return render_template("dust.html", state=ord(session['state'][:1]), username=username,
                         screen=ord(session['state'][1:2]),
                         yes=yes, no=no, abstain=abstain, searchval=session['searchval'])

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
  if 'state' in session:
    del session['state']
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

######################################change password###########################################
######################################change password###########################################
######################################change password###########################################
######################################change password###########################################
######################################change password###########################################
######################################change password###########################################
######################################change password###########################################
######################################change password###########################################

@app.route('/newpass', methods=['POST', 'GET'])
def newpass():
  username=session['username']
  
  if request.method == 'POST':
    current_password = request.form['current_password']
    new_password = request.form['new_password']
    verify_new_password = request.form['verify_new_password']
  
    user = User.query.filter_by(username=username).first()
      
    if(check_pw_hash(current_password,user.hashpass) and new_password==verify_new_password and
       len(new_password) > 0 and len(new_password) < 31):
      #now i'm used to java.  shouldn't the User class have a method to update its password?
      #whatever
      user.hashpass=make_pw_hash(new_password)
      db.session.commit()
      flash("You changed your password.  If you forget it then may God have mercy on your soul.")
    else:
      flash("Something went wrong.  Your password is unchanged.")
    
    return redirect('/')
      
  #just pass username in places like this to make sure you logged them out
  return render_template("newpass.html", username=username)

##########################/demos##################################################################
##########################/demos##################################################################
##########################/demos##################################################################
##########################/demos##################################################################
##########################/demos##################################################################
##########################/demos##################################################################
##########################/demos##################################################################
##########################/demos##################################################################
#this has nothing to do with sinks, just a page to download some old work
@app.route("/demos", methods=['GET'])
def demos():
  if request.method=='GET':
    if request.args.get('demofile') != None:
      demofile=request.args.get('demofile')
      
      try:
        return send_from_directory("../project5", demofile, as_attachment=True)
      except Exception as e:
        return ("<h1>Something went terribly wrong.  Email me if you want.</h1>")
    
    return render_template("demos.html")

#########################################weaselwork###############################################
#########################################weaselwork###############################################
#########################################weaselwork###############################################
#########################################weaselwork###############################################
#########################################weaselwork###############################################
#########################################weaselwork###############################################
#########################################weaselwork###############################################
#########################################weaselwork###############################################
  
#this approute is a mess, never using use it again.  stupid timeouts
#use scripts to update new sinks next time or update averages or anything like that
@app.route('/weaselwork', methods=['GET','POST'])
def weaselwork():
  #never access this route again.  leaving it here as a ruin.
  return redirect('/')
  
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
      #finding total number of sinks.  ...probably a smarter way to do this.  why did i grab location
      total = Sink.query.with_entities(func.count(Sink.id)).first()[0]
      #totalrates=Rating.query.with_entities(func.count(Rating.id)).first()[0]
      #for ix in range(1,total+1):
      for ix in range(10001,total+1):
        sink=Sink.query.filter_by(id=ix).first()
        sink.avg_rating=func.round((Rating.query.with_entities(
          func.avg(Rating.stars).label('average')).filter(Rating.sink_id==sink.id)),2)
        db.session.commit() #hm this works unindented, all those detached sinks...
      flash("10001,total+1")
    elif(orders=="useraverage"):
      total = User.query.with_entities(User.id).order_by(User.id.desc()).first()[0]
      
      for ix in range(1,total+1):
        user=User.query.filter_by(id=ix).first()
        print(ix)
        if user != None:
          print(ix)
          user.avg_rating=func.round((Rating.query.with_entities(
            func.avg(Rating.stars).label('average')).filter(Rating.user_id==user.id)),2)
          db.session.commit()
          #print("user.avg_rating="+str(user.avg_rating))
        
        
    else:
      new_donor=Donator(orders)
      check = Donator.query.filter_by(location=orders).scalar()
      if not check:
        db.session.add(new_donor)
        db.session.commit()
      new_donor = Donator.query.filter_by(location=orders).first()
      
      #time for the hackiest hack ever (502 timeout, don't care about the 'right' way to do
      #it right now
      #ix=0
      
      for root, dirs, files in os.walk(os.path.join("static","sinks",orders),topdown=False):
        #if len(root)<=28:
        #  return root+str(len(root))
        #okay probably scrap next if statement next time updating folder not as massive
        #as silicatewastes
        #if len(root)>28 and root[28].lower() >= 'a' and root[28].lower() <= 'z':
          for val in files:
          #for ix in range(len(files)):
            
            #fun=""
            #for val in files:
            #  fun+=val
            #fun+=" "+root+" "+str(len(files))+" "+str(len(dirs))+" "+root[28]
            #return fun
            
            
            #return str(len(files))
            
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
                #ix+=1
                
      db.session.commit()
      
    #same as in get request, do it again after folder possibly added
    dxfs=[]
    for root, dirs, files in os.walk(os.path.join("static","sinks"), topdown=True):
      for val in dirs:
        dxfs.append(val)
      break
      
    return render_template('weasel.html',title="Weasellwork!", dxfs=dxfs, adds=adds,
                           message=message, username=username)
  
if __name__ == '__main__':
  app.run()

