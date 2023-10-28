
import enum, json


class redisDBIdx(enum.Enum):
   DB_IDX_ONPREM_DIAG = 0
   DB_IDX_EDGE_DIAG = 1
   DB_IDX_READS = 2
   DB_IDX_RUNTIME = 3
   DB_IDX_HEARTBEATS = 4
   DB_IDX_GPIO = 8


"""
   {'type': 'pmessage', 'pattern': 'DEVLAB3RHAT*'
      , 'channel': 'DEVLAB3RHAT_GPIO_OVERRIDE', 'data': 'PIN_DEVLAB3RHAT_CH_1'}
"""
class redisPMsg(object):

   def __init__(self, d: {}):
      _type = d["type"]
      if _type != "pmessage":
         raise Exception(f"BadMsgType: {_type}")
      self.patt: str = d["pattern"]
      self.chnl: str = d["channel"]
      self.data: str = d["data"]

   def __str__(self):
      return f"patt: {self.patt} | chnl: {self.chnl} | data: {self.data}"


class redisChnlPinHash(object):

   def __init__(self, _hash: {}):
      self._hash: {} = _hash
      self.DEVICE_ID: str = ""
      self.CHANNEL_NAME: str = ""
      self.OVERRIDE: str = ""
      self.ON: str = ""
      self.OFF: str = ""
      self.HOLIDAY_ON: str = ""
      self.HOLIDAY_OFF: str = ""
      self.BOARD_CHANNEL: int = 0
      self.__conf__()

   def __str__(self):
      return self._hash

   def __conf__(self):
      # -- -- -- --
      key = "DEVICE_ID"
      if key in self._hash.keys():
         self.DEVICE_ID = self._hash[key]
      # -- -- -- --
      key = "CHANNEL_NAME"
      if key in self._hash.keys():
         self.CHANNEL_NAME = self._hash[key]
      # -- -- -- --
      key = "BOARD_CHANNEL"
      if key in self._hash.keys():
         self.BOARD_CHANNEL = int(self._hash[key])
      # -- -- -- --
      key = "OVERRIDE"
      if key in self._hash.keys():
         self.OVERRIDE = self._hash[key]
      # -- -- -- --
      key = "ON"
      if key in self._hash.keys():
         self.ON = self._hash[key]
      # -- -- -- --
      key = "OFF"
      if key in self._hash.keys():
         self.OFF = self._hash[key]
      # -- -- -- --
      key = "HOLIDAY_ON"
      if key in self._hash.keys():
         self.HOLIDAY_ON = self._hash[key]
      # -- -- -- --
      key = "HOLIDAY_OFF"
      if key in self._hash.keys():
         self.HOLIDAY_OFF = self._hash[key]


# - - - - - - - - - - - - - - - - - - - - - - - -
#
# - - - - - - - - - - - - - - - - - - - - - - - -
class commArgs(object):

   def __init__(self, args: str):
      self.args: str = args
      self.dev: str = ""
      self.comm: str = ""
      self.bus_adr: int = 0
      self.parseOK: bool = False
      # -- -- -- --
      self.br: int = 9600
      self.par: str = "N"
      self.bits: int = 8
      self.__parse__()

   # ";dev:=/run/iotech/dev/modbusPortC;comm:=9600,E,8;busAddr:=8;"
   def __parse__(self):
      try:
         # -- -- -- --
         if self.args[0] != self.args[-1]:
            return
         # -- -- -- --
         tmp: str = self.args[1:-1]
         arr: [] = tmp.split(";")
         self.dev = arr[0].replace("dev:=", "")
         self.comm = arr[1].replace("comm:=", "")
         self.bus_adr: int = int(arr[2].replace("busAddr:=", ""))
         self.parseOK = True
      except Exception as e:
         print(e)
         self.parseOK = False

   def comm_info(self) -> ():
      # -- 9600,8,1,N --
      return self.comm.split(",")


class COMMOptTimeout(Exception):

   def __init__(self):
      super().__init__("COMMOptTimeout")
