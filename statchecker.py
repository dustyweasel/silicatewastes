#maybe kill dustyweasel in mariadb after you're done with this
#make another script like this for updating folders, that weaselwork approute and its timouts suck.
#no my password isn't "asdf", pop a pill

import pymysql
#import os
#import sys
db = pymysql.connect("localhost","dustyweasel","asdf","silicatewastes" )

cursor = db.cursor()

#################### HELPER FUNCTIONS ####################################################

#################### MAIN ####################################################

def main():
    
  #orig_stdout = sys.stdout
  #f = open('out.txt', 'w')
  #sys.stdout = f
  
  getsinkavg = "SELECT SUM(downloads) FROM sink"
  cursor.execute(getsinkavg)
  sinkavg=cursor.fetchall()
  print("total downloads according to sink.downloads = " + str(sinkavg[0][0]))
  
  getuseravg = "SELECT SUM(benefactor) FROM user"
  cursor.execute(getuseravg)
  useravg=cursor.fetchall()
  print("total downloads according to user.benefactor = " + str(useravg[0][0]))

  #sys.stdout = orig_stdout
  #f.close()
  
  db.close()

if __name__ == "__main__":
  main()
