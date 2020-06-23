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
  
  fixdownloads = ("UPDATE sink SET downloads = (SELECT COUNT(*) FROM rating WHERE"+
    " rating.sink_id = sink.id) WHERE sink.downloads < (SELECT COUNT(*) FROM rating WHERE"+
    " rating.sink_id = sink.id)")
  
  print(fixdownloads)
  
  try:
    cursor.execute(fixdownloads)
    db.commit()
    print("success!")
  except Exception as e:
    db.rollback()
    print("failure!")
    print(e)

  #sys.stdout = orig_stdout
  #f.close()
  
  db.close()

if __name__ == "__main__":
  main()
