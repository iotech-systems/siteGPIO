
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
      self.CHANNEL_NAME: str = ""
      self.OVERRIDE: {} = None
      self.CONF: {} = None
      self.CHANNEL_ID: int = 0
      self.__conf__()

   def __conf__(self):
      # -- -- -- --
      key = "CHANNEL_NAME"
      if key in self._hash.keys():
         self.CHANNEL_NAME = self._hash[key]
      # -- -- -- --
      key = "CHANNEL_ID"
      if key in self._hash.keys():
         self.CHANNEL_ID = int(self._hash[key])
      # -- -- -- --
      key = "OVERRIDE"
      if key in self._hash.keys():
         self.OVERRIDE = json.loads(self._hash[key])
      # -- -- -- --
      key = "CONF"
      if key in self._hash.keys():
         self.CONF = json.loads(self._hash[key])
