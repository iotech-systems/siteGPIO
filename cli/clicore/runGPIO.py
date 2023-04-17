
import os
from applib.datatypes import commArgs
from boards.lctech.lct4chModbus import lctech4chModbus
from boards.waveshare.wsh3chHat import waveshare3chHat
from boards.waveshare.wsh8chExpBoard import waveshare8chExpBoard


class runGPIO(object):

   POST_WRITE_DELAY: float = 0.100

   def __init__(self):
      self.board: str = os.getenv("GPIO_BOARD")
      self.dev: str = os.getenv("GPIO_BOARD_DEV")
      self.comm: str = os.getenv("GPIO_BOARD_COMM")
      self.bus_adr: str = os.getenv("GPIO_BOARD_ADR")
      tmp = os.getenv("GPIO_BOARD_SERIAL_DELAY")
      runGPIO.POST_WRITE_DELAY = float(tmp) if (tmp not in [None, ""]) else 0.100

   def init(self):
      print(f"\n\t[ running: gpio ]\n")
      print(f"\t\tBOARD:\t{self.board}")
      init_call = getattr(self, f"__init_{self.board}__")
      if init_call is None:
         print(f"\n[ init call not found: {init_call} ]")
         return
      # -- -- -- --
      init_call()

   def set(self, chnl: int, val: int):
      set_call = getattr(self, f"__set_{self.board}__")
      if set_call is None:
         print(f"\n[ SET call not found: {set_call} ]")
         return
      # -- -- -- --
      set_call(chnl, val)

   def ping(self):
      ping_call = getattr(self, f"__ping_{self.board}__")
      if ping_call is None:
         print(f"\n[ SET call not found: {ping_call} ]")
         return
      # -- -- -- --
      ping_call()

   def __init_lct4r__(self):
      print(f"\t\tCOMM:\t{self.comm}")
      print(f"\t\tADDR:\t{self.bus_adr}")
      x = os.getenv("GPIO_BOARD_SERIAL_DELAY")
      print(f"\t\tSERIAL_DELAY:\t{x}")

   """
      xml_id: str, red: redis.Redis
         , sun: sunClock, args: object):
      "dev:=/run/iotech/dev/modbusPortC;commInfo:=9600,8,1,N;busAddr:=4;"
   """
   def __set_lct4r__(self, chnl, val):
      print("\n\t[ __set_lct4r__ ]")
      args = f";dev:={self.dev};comm:={self.comm};busAddr:={self.bus_adr};"
      print(f"\targs={args}")
      board: lctech4chModbus = lctech4chModbus(xml_id="CLI", args=args)
      board.set_channel(chnl=chnl, val=val)

   def __ping_lct4r__(self):
      print("\n\t[ __ping_lct4r__ ]")
      args = f";dev:={self.dev};comm:={self.comm};busAddr:={self.bus_adr};"
      print(f"\targs={args}")
      board: lctech4chModbus = lctech4chModbus(xml_id="CLI", args=args)
      board.ping()

   def lct4r_set_md_adr(self, old_mb_adr, new_adr):
      print("\n\t[ __set_md_adr_lct4r__ ]")
      args = f";dev:={self.dev};comm:={self.comm};busAddr:={self.bus_adr};"
      print(f"\targs={args}")
      board: lctech4chModbus = lctech4chModbus(xml_id="CLI", args=args)
      board.set_bus_address(old_mb_adr, new_adr)

   def __init_wsh3r__(self):
      print("__init_wsh3r__")

   def __set_wsh3r__(self):
      pass

   def __init_wsh8r__(self):
      print("__init_wsh8r__")

   def __set_wsh8r__(self):
      pass
