#works for ints > 0
def digit(val,val2):
  digits = 1
  digitval =1
  
  while(digits <= val):
    digits *= 10
    digitval +=1
    
  digits = int(digits/10)
  digitval -= 1
  
  #requested digit out of bounds
  if(digitval < val2):
    return 0
  else:
    while(digitval > val2):
      #print("val = "+str(val))
      val -= int(val/digits) * digits
      digitval -=1
      digits = int(digits/10)
      
    val = int(val/digits)
    
  return val

def main():
  val=int(input("enter a positive number: "))
  #2 is tens, 3 is 100's, etc
  val2=int(input("which digit? (1 to infinity): "))
  
  print(digit(val,val2))
  

if __name__ == "__main__":
  main()
