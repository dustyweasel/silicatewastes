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
  elephant = db.relationship('Rating', backref="ratified")
  
  def __init__(self, location, donor):
    self.location=location
    self.downloads=0
    self.donor = donor

class Donator(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  location = db.Column(db.String(60))
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
  dustmask = db.Column(db.Integer)
  benefactor = db.Column(db.Integer)
  lastsink = db.Column(db.Integer)
  memberlevel = db.Column(db.Integer)
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
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
  sink_id = db.Column(db.Integer, db.ForeignKey('sink.id'))
  
  def __init__(self, stars, comment, rater, ratified):
    self.stars=stars
    self.comment=comment
    self.rater=rater
    self.ratified=ratified
    
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
  if (cadfile.lower().endswith('dxf') or cadfile.lower().endswith('.dwg') or
      cadfile.lower().endswith('ard') or cadfile.lower().endswith('.asd') or
      cadfile.lower().endswith('.tag')):
    return True
  else:
    return False

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
    
def reset():
  session['searchval']=""
  session['blanco']=""

#this just grabs a sink location and chops off the donor and folder
#returns truncated location and the sink row
#sets donor and current_folder
def sinksplit(sinkid):
  entry = Sink.query.filter_by(id=sinkid).first()
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
  allowed_routes = ['index', 'login', 'register', 'sink', 'verify', 'chat', 'downloadfile', 'stalk']
  if (request.endpoint not in allowed_routes and 'username' not in session and
    '/static/' not in request.path):
    
    flash("log in, jackass")
    
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
  if request.method == 'GET':
    cloneguys=[]
    if 'donor' in session:
      (guys, session['donor'], cloneguys)=initialize(session['donor'], "")
    else:
      #initial page load
      #folders, current_folder, initial files set further down
      #guys, donor, cloneguys set in initialize
      #need to start current_folder's existence here on initial page load
      #reset searchva, blanco for same reason
      (guys, session['donor'], cloneguys)=initialize("", "")
      reset()
      #quick fix?
      session['current_folder']=""
    
    #if there's no guys for some reason.  should only happen in testing situations.
    if not session['donor']:
      username=""
      if 'username' in session:
        username=session['username']
      return render_template('silicate.html',title="silicatewastes", username=username)

  elif request.method == 'POST':
    #they clicked something.  can't load everything into session so guys
    #needs to be relaoded.  cloneguys gets loaded later.
    (guys, session['donor'], cloneguys)=initialize(session['donor'], "")
    
    if 'home' in request.form:
      reset()
      (guys, session['donor'], cloneguys)=initialize("", "")
    if 'search' in request.form:
      reset()
      session['searchval'] = request.form['searchval']
      if len(session['searchval'])>10:
        flash("enter a filter shorter than 10 chars")
        reset()
        (guys, session['donor'], cloneguys)=initialize("", "")
      elif len(session['searchval'])<1:
        flash("enter something into the search box")
      else:
        flash('Filtering out every filename that does not contain "'+session['searchval']+'"')
      
    elif 'blanco' in request.form:
      reset()
      #why do i initialize twice if blanco and never if search?
      #commented both out, nothing seems to happen
      #(guys, session['donor'], cloneguys)=initialize("", "")
      
      session['blanco'] = request.form['searchval']
      if len(session['blanco'])!=6 or not session['blanco'].isdigit():
        flash("enter a 6 digit number")
        session['blanco']=""
      else:
        session['searchval']=session['blanco']
        
        #just set donor to first guy
        #(guys, session['donor'], cloneguys)=initialize("", "")
          
    if 'other_folder' in request.form:
      session['current_folder']=request.form['other_folder']
    elif 'donor' in request.form:
      newdonor=request.form['donor']
      session['donor']=Donator.query.filter_by(location=newdonor).first().location
        
    if 'chat' in request.form:
      return redirect("/chat")
    elif 'stalk' in request.form:
      return redirect("/stalk")
          
  #this all happens with every call to '/', see indentation above
  #setup cloneguys according to searchval or blanco
  if 'searchval' in session and session['searchval']:
    #for EVERY file
    cloneguys=[]
    if 'blanco' not in session or session['searchval']!=session['blanco']:
      for root, dirs, files in os.walk(os.path.join("static","sinks"), topdown=True):
        for filename in files:
          
          #if ((filename.lower().endswith('dxf') or filename.lower().endswith('.dwg') or
          #     filename.lower().endswith('ard') or filename.lower().endswith('.asd')) and
          #(session['searchval'].lower() in filename.lower())):
          if cadchecker(filename) and session['searchval'].lower() in filename.lower():
           
            #splitter[0]="static"
            #splitter[1]="sinks"
            #splitter[2]="AI"
            #splitter[3]="kohler"
            #splitter[4]="2210" (directory)
            splitter = root.split(os.path.sep)
            newguy = splitter[2]    #AI or whoever
            if newguy not in cloneguys:
              cloneguys.append(newguy)
    else:
      #blanco
      try:
        #a few one off variables here
        #blancopackage and blanco are global
        savesplit=""
        blancofile=open(os.path.join("static","blanco.txt"),'r')
        blancotemp=blancofile.read()
        blancosplit=blancotemp.split("break")
        for ix in range(len(blancosplit)):
          #check for blanco in any of those groups of 8
          if session['blanco'] in blancosplit[ix]:
            #found one
            savesplit=blancosplit[ix]
            break
            
####################################################################################################
        #if we found one
        if savesplit:
          if 'blanco' in request.form:
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
          if 'blanco' in request.form:
            flash("No identical cutouts.  Searching only for "+blancopackage[0]+
                  " and "+blancopackage[1])
####################################################################################################
          
      #i'm a noob at exceptions, this will catch file i/o issues
      #and actually anything else, seen it firsthand
      except Exception as e:
        #this actually didn't work in the yagmail section
        #not sure why it works here
        flash(e)   
      
      #for EVERY file (find out which donors to highlight)
      for root, dirs, files in os.walk(os.path.join("static","sinks"), topdown=True):
        for filename in files:
          #for all 16 matches
          for ix in range(len(blancopackage)):
            #if that 6 digit number with or without hyphen is in a filename
            if blancopackage[ix] in filename:
              #see above, in search
              splitter = root.split(os.path.sep)
              newguy = splitter[2]    #AI or whoever
              if newguy not in cloneguys:
                cloneguys.append(newguy)
              break
    
    #set donor to topmost relevant guy, or top guy if no matches
    if 'search' in request.form or 'blanco' in request.form:
      (guys, session['donor'], cloneguys)=initialize("", cloneguys)
      for ix in range(len(guys)):
        if guys[ix] in cloneguys:
          session['donor']=guys[ix]
          break
  
  folders=[]
  #this only runs on the selected donor
  counter=0
  for root, dirs, files in os.walk(os.path.join("static","sinks",session['donor']), topdown=True):
    
    #if no search or donor dumps all files into his root directory
    if not session['searchval'] or (counter==0 and len(dirs)==0):
      for val in dirs:
        folders.append(val)
      break
    
    #only on loops 1 to infinity
    #(for every file in donor's directory EXCEPT root directory)
    #if blanco match mode
    if counter>0 and session['searchval'] and session['searchval']==session['blanco']:
      for filename in files:
        if cadchecker(filename):
        #if (filename.lower().endswith('dxf') or filename.lower().endswith('.dwg') or
        #    filename.lower().endswith('ard') or filename.lower().endswith('.asd')):
          #see above for how this works
          for ix in range(len(blancopackage)):
            if blancopackage[ix] in filename:
              splitter = root.split(os.path.sep)
              newfolder = splitter[3] #"kohler" or whatever
              if newfolder not in folders:
                folders.append(newfolder)
              break
    
    #if search mode and loops 1 to infinity
    elif counter>0 and session['searchval']:
      for filename in files:
        if cadchecker(filename) and session['searchval'].lower() in filename.lower():
        #if ((filename.lower().endswith('dxf') or filename.lower().endswith('.dwg') or
        #     filename.lower().endswith('ard') or filename.lower().endswith('.asd')) and
        #session['searchval'].lower() in filename.lower()):
          
          splitter = root.split(os.path.sep)
          
          newfolder = splitter[3] #kohler or whatever
          if newfolder not in folders:
            folders.append(newfolder)
    
    counter+=1
  folders.sort(key=lambda x: x.lower())
    
  #current_folder finally set here to top folder or no folder
  if not session['current_folder'] or (request.method ==  'POST' and
                                       ('donor' in request.form or'search' in request.form or
                                        'blanco' in request.form or 'home' in request.form)):
    
    #they picked something besides a folder, set current_folder to top available folder
    if len(folders)>0:
      session['current_folder']=folders[0]
    else:
      session['current_folder']=""
  
  #fill up initial_files
  #if current_folder is an emptry string os.path.join slaps on a damn '/'
  if session['current_folder']:
    newpath=os.path.join("static","sinks",session['donor'],session['current_folder'])
  else:
    newpath=os.path.join("static","sinks",session['donor'])
  
  #for every file in current_folder
  initial_files=[]
  for root, dirs, files in os.walk(newpath, topdown=True):
    for val in files:
      if cadchecker(val):
      #if (val.lower().endswith('.dxf') or val.lower().endswith('.dwg') or
      #val.lower().endswith('.ard')
      #  or val.lower().endswith('.asd')):
        
        newval=""
        #if no search then grab them all else only grab the matches
        #seriously speeds things up if skip non-matches
        if not session['searchval'] or (session['searchval'] and session['searchval'].lower()
                                       in val.lower()):
          newval=os.path.join(root,val)
        #blanco match
        elif session['searchval'] and session['searchval']==session['blanco']:
          for ix in range(len(blancopackage)):
            if blancopackage[ix] in val:
              newval=os.path.join(root,val)
              break
        
        #if no search or matches on search
        if newval:
          rated_sink = Sink.query.filter_by(location=newval[13:]).first()
          ratings = Rating.query.filter_by(sink_id=rated_sink.id).all()
          ival=0
          for blah in range(len(ratings)):
            ival+=ratings[blah].stars
          if len(ratings) == 0:
            ival=-1
          else:
            ival=round(float(ival)/float(len(ratings)),1)
          if(folders):
            newval=newval[14+len(os.path.join(session['donor'],session['current_folder'])):]
          else:
            newval=newval[14+len(session['donor']):]
          
          initial_files.append((newval,ival,rated_sink.id))

  #i only half understand this
  initial_files = sorted(initial_files, key=lambda tup: tup[0].lower())
   
  username=""
  if 'username' in session:
    username=session['username']

  return render_template('silicate.html',title="silicatewastes", guys=guys,
                         cloneguys=cloneguys, folders=folders,
                         cads=initial_files, donor=session['donor'],
                         current_folder=session['current_folder'], username=username,
                         staticsearchval=session['searchval'], blanco=session['blanco'])

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
  #if url makes sense, load the sink row grab the truncated location
  if request.method == 'GET' and request.args.get('cad') != None:
    #this int cast will crash it if some knucklhead messes with the url.
    #i WANT it to crash in this situation
    cad = int(request.args.get('cad'))
    #not gonna check if they entered too large of an int.  just let the query fail.
  #if post request same thing
  elif request.method == 'POST' and 'cad' in request.form:
    cad = int(request.form['cad'])
    
  #else he's messing with the URL or something's messed up.
  else:
    return redirect('/')
  
  #regardless of request type, set sink to truncated location
  #sinkentry to sink row
  (sink,sinkentry)=sinksplit(cad)
    
  new_rating=""
  previous_sink=""
  username=""
  previous_rating=""
  
  if request.method=='POST' and 'username' in session:
    username=session['username']
    user = User.query.filter_by(username=username).first()
    
    
    #clear out lastsink, stop bothering user about it
    if 'forgot' in request.form:
      user.lastsink=0
      db.session.commit()
    if user.lastsink!=0:
      previous_sink = Sink.query.filter_by(id=user.lastsink).first()
      #see if he rated the last sink he downloaded
      previous_rating = Rating.query.filter_by(user_id=user.id, sink_id=previous_sink.id).first()
      #if it's already rated then don't bother him
      if previous_rating!=None:
        previous_sink=""
        
      #he clicked add rating on previous sink
      elif 'rate_previous' in request.form:
        if 'starsB' not in request.form:
          flash("pick a rating")
        else:
          stars = request.form['starsB']
          comment = request.form['commentB']
          if len(comment)>60:
            flash("comment must be less than 60 chars")
          #stick in the new rating, stop bothering him about it
          else:
            #previous_rating points to an actual row that you want to change
            #thats why you don't want a new variable called new_rating here
            previous_rating = Rating(stars, comment, user, previous_sink)
            db.session.add(previous_rating)
            db.session.commit()
            previous_rating=""
            previous_sink=""
            flash("THANKS!")
  
  #add rating to current sink
  #(this corresponds to the sink in the url, not a sink pulled from the user's last
  #download variable, like above)
  if request.method=='POST' and 'add' in request.form:
    comment = request.form('comment')
    if len(comment)>60:
      flash("comment must be less than 60 chars")
    else:
      #redundant?  maybe safeguards against hackers.
      if username:
        #load the rating we're changing (if it exists)
        new_rating = Rating.query.filter_by(user_id=user.id, sink_id=sinkentry.id).first()
      
      if 'stars' in request.form:
        stars = request.form['stars']
        #overwrite pre-existing rating
        if new_rating:
          new_rating.stars=stars
          new_rating.comment=comment
          new_rating.user=user
          new_rating.sink=sinkentry
          db.session.commit()
        #put in brand new rating
        else:
          new_rating=Rating(stars, comment, user, sinkentry)
          db.session.add(new_rating)
          db.session.commit()
      else:
        flash("You didn't pick a rating.")
  elif request.method=='POST' and 'change' in request.form:
    #just delete it
    user_rating = Rating.query.filter_by(user_id=user.id, sink_id=sinkentry.id).first()
    db.session.delete(user_rating)
    db.session.commit()
  
  user_rating=""
  if username:
    #now load up their rating
    user_rating = Rating.query.filter_by(user_id=user.id, sink_id=sinkentry.id).first()
    
  #load up all ratings, just filter out user rating in jinja.  probably smarter to do
  #it here or in the query directly above but i'll figure it out some other day
  ratings = Rating.query.filter_by(sink_id=sinkentry.id).all()
  
  return render_template("sink.html", folder=session['current_folder'], donor=session['donor'],
                         sink=sink, ratings=ratings, username=username, user_rating=user_rating,
                         previous_sink=previous_sink)


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
  session['current_folder'] = request.form['current_folder']
  sink = request.form['sink']

  if 'cancel' in request.form:
    return redirect("/")

  #same old check if donor dumped all his cads in his root directory
  if(session['current_folder']):
    location=os.path.join(session['donor'],session['current_folder'],sink)
  else:
    location=os.path.join(session['donor'],sink)

  sinkentry = Sink.query.filter_by(location=location).first()

  if 'username' in session:
    username = session['username']
    user = User.query.filter_by(username=username).first()
    
    try:
      sinkentry.downloads+=1
      user.lastsink=sinkentry.id
      #user downloads.  made that variabe for something else.  whatever.
      user.benefactor+=1
      db.session.commit()
      
      return send_from_directory(os.path.join("static","sinks",session['donor'],
                                  session['current_folder']), sink, as_attachment=True)
    except Exception as e:
      return ("<h1>Something went terribly wrong.  Email me all this if you want:<br/>"+
              os.path.join("static","sinks",session['donor'],session['current_folder'])+
              "&nbsp&nbsp&nbsp"+sink+"<br/><br/>"+str(e)+"<h1>")
  else:
    username=""
    flash("log in, jackass")
    
  ratings = Rating.query.filter_by(sink_id=sinkentry.id).all()
  user_rating=""

  #don't need previous sink
  return render_template("sink.html", folder=session['current_folder'], donor=session['donor'],
                         sink=sink, ratings=ratings, username=username, user_rating=user_rating)

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
  username=""
  if 'username' in session:
    username=session['username']
  
  if request.method == 'POST':
    if 'babble' in request.form:
      if username:
        babble = request.form['babble']
        if len(babble)>60 or len(babble)<2:
          flash("babblings must be 2-60 chars")
        else:
          ref_user = user = User.query.filter_by(username=username).first()
          new_babble = Babblings(babble, ref_user)
          
          db.session.add(new_babble)
          db.session.commit()
      else:
        flash("log in, jackass")
  prebabblings = Babblings.query.order_by(Babblings.id.desc()).all()
  babblings=[]
  for ix in range(len(prebabblings)):
    babblings.append((ix%2, prebabblings[ix]))
    
  babble="annoying"
  
  return render_template("chat.html", babblings=babblings, username=username, babble=babble)

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
    
  members=User.query.with_entities(User.id, User.username, User.catchphrase, User.memberlevel,
                                   User.benefactor, User.state, User.company).all()
  #if request.method == 'GET':
  #if request.method == 'POST':
  #if 'search' in request.form:
      #session['searchval'] = request.form['searchval']
  #guy = request.args.get('guy')
  if request.method == 'POST':
    if 'username' not in session:
      flash("log in, jackass")
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
      
  elif request.method == 'GET':
    if request.args.get('member') != None:
      #if it's not an int, let it crash
      member = int(request.args.get('member'))
      if 'username' not in session:
        flash("log in, jackass")
      else:
        memberdata=User.query.filter_by(id=member).first()
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
       
            
        return render_template("stalkmore.html", stalk="stalk", memberdata=memberdata,
                              memberratings=memberratings, username=username)
  
  
  return render_template("stalk.html", stalk="stalk", members=members, username=username)

#@app.route('/stalkmore', methods=['GET'])
#def stalkmore():
  #members=User.query.with_entities(User.id, User.username, User.catchphrase, User.memberlevel,
  #                                 User.benefactor, User.state, User.company).all()
  #loadguys=Donator.query.all()
  
#  return render_template("stalkmore.html", stalk="stalk")

################################login###########################################################
################################login###########################################################
################################login###########################################################
################################login###########################################################
################################login###########################################################
################################login###########################################################
################################login###########################################################
################################login###########################################################

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

@app.route('/register', methods=['POST', 'GET'])
def register():
  allset=True
  
  username=""
  password=""
  verify=""
  email=""
  company=""
  catchphrase=""
  
  if request.method == 'POST':
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
      flash("enter an email address, jackass")
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
        session['secret_pass']=""
        return redirect('/')
        
      #if form data is good
      #session['tempuser']=new_user
      session['password']=password
      flash("YOU ENTERED: "+email)
      return render_template("verify.html", user=new_user)
    else:
      username=""
  
  return render_template("register.html", username=username, email=email, company=company,
              catchphrase=catchphrase)

@app.route('/verify', methods=['POST'])
def verify():
  username = request.form['username']
  #password = request.form['password']
  email = request.form['email']
  company = request.form['company']
  catchphrase = request.form['catchphrase']
  usstate = request.form['state']
  secretpass = request.form['secretpass']
  if 'dust' not in request.form:
    dust=3
  else:
    dust = request.form['dust']
    
  new_user = User(username, session['password'], email, company, catchphrase, usstate, dust)
  del session['password']
  
  if secretpass == session['secret_pass']:
    flash("Welcome to the silicate wastes, "+username+".")
    db.session.add(new_user)
    db.session.commit()
    session['username'] = new_user.username
  else:
    flash("Wrong secret key.  Start over.")
    
  session['secret_pass']=""
  username=""
  return redirect('/')

@app.route('/logout')
def logout():
  del session['username']
  return redirect('/')

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

