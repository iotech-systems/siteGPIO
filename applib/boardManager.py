
import threading, typing as t
import xml.etree.ElementTree as _et
import redis, configparser as _cp
from applib.sunclock import sunClock
# -- import system gpio boards --
from boards.waveshare.wsh3chHat  import waveshare3chHat
from boards.waveshare.wsh8chExpBoard import waveshare8chExpBoard
from boards.lctech.lct4chModbus import lctech4chModbus


class boardManager(object):

   def __init__(self, ini: _cp.ConfigParser
         , sun: sunClock
         , red: redis.Redis
         , xml: _et.Element):
      # -- -- -- --
      self.ini: _cp.ConfigParser = ini
      self.sun: sunClock = sun
      self.red: redis.Redis = red
      self.xml: _et.Element = xml
      self.board_bots: t.List[threading.Thread] = []

   def init(self) -> bool:
      _boards: t.List[_et.Element] = self.xml.findall("boards/board")
      # -- oneach call --
      def _oneach(e: _et.Element) -> threading.Thread:
         # -- -- -- ---
         _id = e.attrib["id"]
         _args = e.attrib["args"]
         _type = e.attrib["type"]
         # -- -- -- ---
         if _type == "waveshare3chHat":
            board: waveshare3chHat = \
               waveshare3chHat(xml_id=_id, red=self.red, sun=self.sun, args=_args)
            board.init()
            return board
         # -- -- -- ---
         elif _type == "waveshare8chExpBoard":
            board: waveshare8chExpBoard = \
               waveshare8chExpBoard(xid=_id, red=self.red, sun=self.sun, args=_args)
            board.init()
            return board
         # -- -- -- ---
         elif _type == "lctech4chModbus":
            board: lctech4chModbus = \
               lctech4chModbus(xml_id=_id, red=self.red, sun=self.sun, args=_args)
            board.init()
            return board
         # -- -- -- ---
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
