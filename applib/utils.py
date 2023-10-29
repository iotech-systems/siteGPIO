
import serial, typing as t
import datetime, calendar as cal
import socket, os, time, re
from serial.tools import list_ports
from termcolor import colored
from applib.datatypes import *


class utils(object):

   HOST_TZ: str = ""
   GEOLOC = ""
   BUILDING = ""
   with open("/etc/hostname") as f:
      HOST = f.read().strip()

   def __init__(self):
      pass

   @staticmethod
   def usbPorts():
      ports = list_ports.comports()
      return [p for p in ports if ("USB" in p.name.upper())]

   @staticmethod
   def lan_ip():
      try:
         s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
         s.connect(("8.8.8.8", 80))
         lan_ip = s.getsockname()[0]
         s.close()
         return lan_ip
      except Exception as e:
         print(e)
      finally:
         pass

   @staticmethod
   def dts_utc(with_tz: bool = False):
      d = datetime.datetime.utcnow()
      buff = f"{d.year}-{d.month:02d}-{d.day:02d}T" \
         f"{d.hour:02d}:{d.minute:02d}:{d.second:02d}"
      return buff if with_tz is False else f"{buff} UTC"

   @staticmethod
   def ts_utc():
      _t = datetime.datetime.utcnow()
      return f"{_t.hour:02d}:{_t.minute:02d}:{_t.second:02d}"

   @staticmethod
   def dts_local():
      d: datetime = datetime.datetime.now()
      buff = f"{d.year}-{d.month:02d}-{d.day:02d}T" \
         f"{d.hour:02d}:{d.minute:02d}:{d.second:02d}"
      return f"{buff}"

   @staticmethod
   def host_tz_info():
      if utils.HOST_TZ in [None, ""]:
         with open("/etc/timezone", "r") as f:
            utils.HOST_TZ = f.read().strip()
      return utils.HOST_TZ

   @staticmethod
   def syspath(channel: str, endpoint: str):
      try:
         if utils.GEOLOC == "":
            with open("/etc/iotech/geoloc") as f:
               utils.GEOLOC = f.read().strip()
         if utils.BUILDING == "":
            with open("/etc/iotech/building") as f:
               utils.BUILDING = f.read().strip()
         if utils.HOST == "":
            with open("/etc/hostname") as f:
               utils.HOST = f.read().strip()
         # -- -- -- --
         return f"/{utils.GEOLOC}/{utils.BUILDING}/{utils.HOST}/{channel}/{endpoint}"
      except Exception as e:
         print(e)
         exit(1)

   @staticmethod
   def min_dts() -> datetime.datetime:
      return datetime.datetime.fromisoformat("0001-01-01T01:01:01")

   @staticmethod
   def next_month_day_date(y: int, m: int, d: int = 1) -> datetime.date:
      if m == 12:
         y += 1
         m = 1
      # -- return date --
      return datetime.date(y, m, d)

   @staticmethod
   def next_month_day_str(y: int, m: int, d: int = 1) -> str:
      if m == 12:
         y += 1; m = 1
      else:
         m += 1
      # -- return date --
      return f"{y}-{m:02d}-{d:02d}"

   @staticmethod
   def dts_now():
      d = datetime.datetime.utcnow()
      return f"{d.year}-{d.month:02d}-{d.day:02d}" \
         f" {d.hour:02d}:{d.minute:02d}:{d.second:02d}"

   @staticmethod
   def get_run_id():
      tme = int(time.time())
      return f"0x{tme:08x}"

   @staticmethod
   def year_month_days(y: int, m: int):
      return cal.monthrange(y, m)[1]

   @staticmethod
   def pin_redis_key(devid: str, chnl: str):
      return f'PIN_{devid}_ch_{chnl}'.upper()

   @staticmethod
   def decode_redis(src):
      if isinstance(src, list):
         rv = list()
         for key in src:
            rv.append(utils.decode_redis(key))
         return rv
      elif isinstance(src, dict):
         rv = dict()
         for key in src:
            rv[key.decode()] = utils.decode_redis(src[key])
         return rv
      elif isinstance(src, bytes):
         return src.decode()
      else:
         raise Exception("type not handled: " + type(src))

   @staticmethod
   def printf(m: str, col: str, bold: bool = False
         , with_ts: bool = True, pre: str = "", post: str = ""):
      # -- -- -- --
      _m: str = f"{pre}{m}{post}"
      if with_ts:
         _m = f"{pre}[ {utils.dts_local()} | {m} ]{post}"
      # -- -- -- --
      _bold = "bold" if bold else ""
      print(colored(_m, color=col, attrs=[_bold]))
