
import datetime
from applib.sunclock import DAY_PARTS


class clock(object):

   @staticmethod
   def is_good_time(time_str: str) -> bool:
      if time_str in DAY_PARTS:
         return True
      # -- test string --
      arr = time_str.split(":")
      if len(arr) != 2:
         raise Exception("bad arr")
      hr: int = int(arr[0])
      mn: int = int(arr[1])
      if hr not in range(0, 24):
         raise Exception("bad hr")
      if mn not in range(0, 60):
         raise Exception("bad mn")
      return True

   @staticmethod
   def get_state(ont: str, oft: str) -> bool:
      time_on: datetime.time = clock.get_time(ont)
      time_off: datetime.time = clock.get_time(oft)
      # -- calc --
      time_now = datetime.datetime.now().time()
      # -- if in 24 hrs --
      if time_on < time_off:
         return time_on < time_now < time_off
      # -- if off next day --
      elif time_off < time_on:
         return (time_on < time_now) or (time_now < time_off)
      else:
         return False

   @staticmethod
   def get_time(tme: [datetime.time, str]) -> datetime.time:
      if isinstance(tme, datetime.time):
         return tme
      # -- parse string --
      arr = tme.split(":")
      if len(arr) == 2:
         hr, mn = arr
      elif len(arr) == 3:
         hr, mn, _ = arr
      else:
         raise Exception(f"BadTimeFormat: {tme}")
      # -- --
      hr: int = int(hr); mn: int = int(mn)
      return datetime.time(hour=hr, minute=mn, second=0, microsecond=0)
