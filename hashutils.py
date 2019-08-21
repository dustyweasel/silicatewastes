import hashlib
import random
import string

def make_salt():
  #from launchcode salting video, haven't bothered understanding this yet
  return ''.join([random.choice(string.ascii_letters) for x in range(5)])

def make_pw_hash(password, salt=None):
  if not salt:
    salt = make_salt()
  hashval = hashlib.sha256(str.encode(password + salt)).hexdigest()
  
  return '{0},{1}'.format(hashval,salt)
  
def check_pw_hash(password, hashval):
  salt = hashval.split(',')[1]
  
  if make_pw_hash(password,salt) == hashval:
    return True
  else:
    return False
