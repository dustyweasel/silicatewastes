#this is just a script to kill off 1000's of duplicate files that that i stupidly uploaded
#remember to kill dustyweasel in mariadb after you're done with this
#make another script like this for updating folders, that weaselwork approute and its timouts suck.

import pymysql
import os
import sys
db = pymysql.connect("localhost","dustyweasel","asdf","silicatewastes" )

cursor = db.cursor()

#################### HELPER FUNCTIONS ####################################################

def cadchecker(cadfile):
  if (cadfile.lower().endswith('.dxf') or cadfile.lower().endswith('.dwg') or
      cadfile.lower().endswith('.ard') or cadfile.lower().endswith('.asd') or
      cadfile.lower().endswith('.tag') or cadfile.lower().endswith('.est')):
    return True
  else:
    return False

#should have called this de-underscorer
def hyphenator(cadfile):
  copyfile=""
  for ix in range(len(cadfile)):
    if cadfile[ix] != '_':
      copyfile+=cadfile[ix]
    else:
      copyfile+=' '
    
  return copyfile
    

#################### MAIN ####################################################

def main():
  
  folders=[]
  folder=""
  for root, dirs, files in os.walk(os.path.join("static","sinks"), topdown=True):
    folders=dirs
    break
  
  for ix in range(len(folders)):
    print(str(ix+1)+' '+folders[ix])
    
  val = int(input("which folder to de-underscore? "))
  if val<1 or val>len(folders):
    print("out of range, dumbass")
    return
  else:
    folder=folders[val-1]
    
  orig_stdout = sys.stdout
  f = open('out.txt', 'w')
  sys.stdout = f
  
  for root, dirs, files in os.walk(os.path.join("static","sinks",folder), topdown=True):
    for val in files:
      if cadchecker(val):
        for root2, dirs2, files2 in os.walk(root, topdown=True):
          for val2 in files2:
            if cadchecker(val2) and val != val2 and val == hyphenator(val2):
              #val2 is the underscore version
              print(root+" "+val+" "+val2)
              getsink1 = "SELECT id FROM sink WHERE location = '" + os.path.join(root,val)[13:] +"'"
              getsink2 = "SELECT id FROM sink WHERE location = '" + os.path.join(root,val2)[13:] +"'"
              cursor.execute(getsink1)
              rated_sink1=cursor.fetchall()
              print(rated_sink1[0][0])
              cursor.execute(getsink2)
              rated_sink2=cursor.fetchall()
              print(rated_sink2[0][0])
              
              getratings1 = "SELECT * FROM rating WHERE sink_id = " + str(rated_sink1[0][0])
              getratings2 = "SELECT * FROM rating WHERE sink_id = " + str(rated_sink2[0][0])
              
              cursor.execute(getratings1)
              ratings1=cursor.fetchall()
              for rating in ratings1:
                print(str(rating[0])+' '+str(rating[1])+' '+rating[2]+' '+str(rating[3])+
                                             ' '+str(rating[4]))
              cursor.execute(getratings2)
              ratings2=cursor.fetchall()
              for rating in ratings2:
                print(str(rating[0])+' '+str(rating[1])+' '+rating[2]+' '+str(rating[3])+
                                             ' '+str(rating[4]))
              
              if len(ratings2) == 0:
                print("underscore version has no ratings, deleting it")
                print(os.path.join(root,val2))
                os.remove(os.path.join(root,val2))
                deleteunderscore = "DELETE FROM sink WHERE id = " + str(rated_sink2[0][0])
                print(deleteunderscore)
                try:
                  cursor.execute(deleteunderscore)
                  db.commit()
                except:
                  db.rollback()
              elif len(ratings1) == 0:
                print("space version has no ratings, but underscore version does, copying over")
                for rating in ratings2:
                  swaprating=("UPDATE rating SET sink_id = " + str(rated_sink1[0][0]) +
                              " WHERE id = " + str(rating[0]))
                  print(swaprating)
                  try:
                    cursor.execute(swaprating)
                    db.commit()
                  except:
                    db.rollback()
                print("sticking new avg into space version")
                getaverage = ("SELECT ROUND(AVG(stars),1) FROM rating WHERE sink_id = " +
                              str(rated_sink1[0][0]))
                print(getaverage)
               
                cursor.execute(getaverage)
                average=cursor.fetchall()
                print(str(average[0][0]))
                setaverage=("UPDATE sink SET avg_rating = " + str(average[0][0]) +
                            " WHERE id = " + str(rated_sink1[0][0]))
                print(setaverage)
                try:
                  cursor.execute(setaverage)
                  db.commit()
                  print("success!")
                except Exception as e:
                  db.rollback()
                  print("failure!")
                  print(e)
                  
                    
                print("and deleting underscore version")
                
                #same as above
                print(os.path.join(root,val2))
                os.remove(os.path.join(root,val2))
                deleteunderscore = "DELETE FROM sink WHERE id = " + str(rated_sink2[0][0])
                print(deleteunderscore)
                try:
                  cursor.execute(deleteunderscore)
                  db.commit()
                except:
                  db.rollback()
                  
          break #breaks val2 loop, only search for matches in that one folder
        
  sys.stdout = orig_stdout
  f.close()
  
  db.close()

if __name__ == "__main__":
  main()
