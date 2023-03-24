
from applib.sunclock import sunClock
from applib.datatypes import redisChnlPinHash


class channelPinDriver(object):

   def __init__(self, red_hash: redisChnlPinHash
         , sun: sunClock
         , active_state: int = 1):
      # -- -- -- -- -- -- -- --
      self.red_hash: redisChnlPinHash = red_hash
      self.sun: sunClock = sun
      self.active_state: int = active_state

   def get_state(self) -> str:
      override_state: str = self.__get_override__()
      if override_state is not None:
         return override_state
      # -- -- -- --
      calc_state: str = self.__calc_conf_state__()
      return calc_state

   def __get_override__(self) -> [None, int]:
      if self.red_hash.OVERRIDE is None:
         return None
      state: str = str(self.red_hash.OVERRIDE["state"]).upper()
      if state not in ("ON", "OFF"):
         return None
      # -- -- -- --
      return state

   def __calc_conf_state__(self) -> str:
      _none: [] = [None, ""]
      _off = "OFF"; _on = "ON"
      if self.red_hash.CONF is None:
         return _off
      # -- -- -- --
      tOn: str = self.red_hash.CONF["tON"]
      tOff: str = self.red_hash.CONF["tOFF"]
      sOn: str = self.red_hash.CONF["sunOn"]
      sOff: str = self.red_hash.CONF["sunOff"]
      sOnOffset: int = int(self.red_hash.CONF["sunOnOffset"])
      sOffOffset: int = int(self.red_hash.CONF["sunOffOffset"])
      # -- start time not set! --
      if tOn in _none and sOn in _none:
         return _off
      if tOff in _none and sOff in _none:
         return _off
      # -- -- -- --
      _time_on = sOn if tOn in _none else tOn
      _time_off = sOff if tOff in _none else tOff
      # -- -- -- --
      print([_time_on, _time_off])
      self.sun.is_sun_format(_time_on)
      return _off
