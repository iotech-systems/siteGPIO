
import threading


class threadBot(threading.Thread):

   def __init__(self):
      super().__init__()

   def run(self) -> None:
      pass

   def __str__(self):
      return "threadBot ver. 001"
