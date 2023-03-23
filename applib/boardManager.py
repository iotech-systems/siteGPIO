
import threading, typing as t
import xml.etree.ElementTree as _et
import redis, configparser as _cp
from boards.waveshare3chHat import waveshare3chHat
from boards.lctech4chModbus import lctech4chModbus


class boardManager(object):

   def __init__(self, ini: _cp.ConfigParser
         , red: redis.Redis
         , xml: _et.Element):
      # -- -- -- --
      self.ini: _cp.ConfigParser = ini
      self.red: redis.Redis = red
      self.xml: _et.Element = xml
      self.board_bots: t.List[threading.Thread] = []

   def init(self) -> bool:
      _boards: t.List[_et.Element] = self.xml.findall("boards/board")
      # -- oneach call --
      def _oneach(e: _et.Element) -> threading.Thread:
         _id = e.attrib["id"]; _args = e.attrib["args"]
         _type = e.attrib["type"]
         if _type == "waveshare3chHat":
            board: waveshare3chHat = waveshare3chHat(xid=_id, red=self.red, args=_args)
            board.init()
            return board
         elif _type == "lctech4chModbus":
            board: lctech4chModbus = lctech4chModbus(xid=_id, red=self.red, args=_args)
            board.init()
            return board
         else:
            raise Exception(f"BadBoardType: {_type}")
      # -- create list --
      self.board_bots = [_oneach(b) for b in _boards]
      return len(_boards) == len(self.board_bots)

   def start(self) -> bool:
      accu: bool = True
      for b in self.board_bots:
         try:
            b: threading.Thread = b
            b.start()
            accu &= True
         except:
            accu &= False
      # -- -- -- --
      return accu
