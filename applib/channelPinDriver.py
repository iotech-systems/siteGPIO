
import calendar as cal
import datetime as dt
from applib.clock import clock
from applib.sunclock import sunClock
from applib.datatypes import redisChnlPinHash


class channelPinDriver(object):

   ON: str = "ON"
   OFF: str = "OFF"
   ON_OFF: [] = [ON, OFF]

   def __init__(self, red_hash: redisChnlPinHash
         , sun: sunClock
         , holidays: [] = None
         , active_state: int = 1):
      # -- -- -- -- -- -- -- --
      self.red_hash: redisChnlPinHash = red_hash
      self.holidays: [] = holidays
      self.sun: sunClock = sun
      self.active_state: int = active_state

   def get_state(self) -> str:
      # -- -- -- --
      override_state: str = self.__get_override__()
      if override_state is not None:
         return override_state
      # -- -- -- --
      if not self.__is_good_input__():
         return channelPinDriver.OFF
      # -- -- -- --
      calc_state: str = self.__calc_clock_state__()
      return calc_state

   def __get_override__(self) -> [None, int]:
      if self.red_hash.OVERRIDE in [None, "NIL"]:
         return None
      state: str = str(self.red_hash.OVERRIDE.upper())
      if state not in channelPinDriver.ON_OFF:
         return None
      # -- -- -- --
      return state

   def __calc_clock_state__(self) -> str:
      _off = "OFF"; _on = "ON"
      _none: [] = [None, "", "NIL"]
      # -- -- -- --
      is_holiday: bool = self.__is_holiday
      onHH, onMM = self.red_hash.ON.split(":")
      if is_holiday:
         onHH, onMM = self.red_hash.HOLIDAY_ON.split(":")
      timeOn = f"{onHH}:{onMM}"
      if sunClock.is_sun_format(onHH):
         timeOn = self.sun.get_time(onHH, int(onMM))
      # -- -- -- --
      offHH, offMM = self.red_hash.OFF.split(":")
      if is_holiday:
         offHH, offMM = self.red_hash.HOLIDAY_OFF.split(":")
      timeOff = f"{offHH}:{offMM}"
      if sunClock.is_sun_format(offHH):
         timeOff = self.sun.get_time(offHH, int(offMM))
      # -- -- -- --
      state: bool = clock.get_state(timeOn, timeOff)
      return _on if state else _off

   def __is_good_input__(self):
      if self.red_hash.ON in [None, ""]:
         return False
      # -- --
      onHH, onMM = self.red_hash.ON.split(":")
      timeOn = f"{onHH}:{onMM}"
      offHH, offMM = self.red_hash.OFF.split(":")
      timeOff = f"{offHH}:{offMM}"
      # -- --
      return not (timeOn == timeOff)

   @property
   def __is_holiday(self) -> bool:
      _today = dt.datetime.today()
      _isoweekday: int = _today.isoweekday()
      dname: str = cal.day_name[(_isoweekday - 1)]
      print(f"[ __is_holiday: isoweekday/ {dname} ]")
      if _isoweekday in [6, 7]:
         print("[ TheWeekend! ]")
         return True
      # -- --
      month, day = _today.month, _today.day
      if self.holidays is None or len(self.holidays) == 0:
         print(f"[ __is_holiday: None ]")
         return False
      # -- --
      arr: [] = [d for d in self.holidays if int(d["m"]) == month and int(d["d"]) == day]
      print(f"arr: {arr}")
      return len(arr) > 0
