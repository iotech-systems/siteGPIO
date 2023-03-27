
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
      self.BOARD_CHANNEL: int = 0
      self.__conf__()

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
         self.OVERRIDE = self._hash["OVERRIDE"]
      # -- -- -- --
      key = "ON"
      if key in self._hash.keys():
         self.ON = self._hash["ON"]
      # -- -- -- --
      key = "OFF"
      if key in self._hash.keys():
         self.OFF = self._hash["OFF"]
