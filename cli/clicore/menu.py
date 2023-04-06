
import os, time
import cli.clicore.clihelp as _chlp


class mainMenu(object):

   def __init__(self):
      pass

   def menu0(self):
      while True:
         os.system("clear")
         print(_chlp.SYS_MM)
         sel = input("\t?: ")
         print(f"\t: {sel}")
         # -- -- -- -- -- -- -- --
         if int(sel) not in [1, 2]:
            print(f"BadSelection: {sel}")
         # -- -- -- -- -- -- -- --
         call = f"menu0_{sel}"
         try:
            self_method = getattr(self, call)
            self_method()
            time.sleep(2.0)
         except Exception as e:
            print(e)

   def menu0_1(self):
      os.system("clear")
      print("\n\t[ select GPIO board ]")

   def menu0_2(self):
      os.system("clear")
      print("+ menu0_1")

   def menu0_1_1(self):
      os.system("clear")
