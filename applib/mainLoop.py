
from applib.boardManager import boardManager


class mainLoop(object):

   def __init__(self, **kwargs):
      pass

   def loop_tick(self, **kwargs) -> int:
      bm: boardManager = kwargs["board_man"]
      return 0
