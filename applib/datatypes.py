
import enum

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
