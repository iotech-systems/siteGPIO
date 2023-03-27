
import time, redis
import os, threading
from applib.utils import utils
from applib.datatypes import redisDBIdx, redisPMsg, redisChnlPinHash
from applib.interfaces.rpiHatBoard import rpiHatBoard
from applib.channelPinDriver import channelPinDriver
from applib.sunclock import sunClock
# "armv7l": on running on RPi
if os.uname()[4].startswith("armv"):
   import RPi.GPIO as GPIO
   GPIO.setwarnings(False)
else:
   from sims.rpiGPIO import GPIO


"""
   BCM |  wPi | gpio
   26  |  25  | GPIO.25 -> CH1
   20  |  28  | GPIO.28 -> CH2
   21  |  29  | GPIO.29 -> CH3
"""
class waveshare3chHat(rpiHatBoard, threading.Thread):

   def __init__(self, xid: str
         , red: redis.Redis
         , sun: sunClock
         , args: object):
      # -- -- -- -- -- -- --
      threading.Thread.__init__(self)
      super().__init__()
      self.id = xid
      self.board_id = self.id.upper()
      self.red: redis.Redis = red
      self.red_sub = self.red.pubsub()
      self.red_sbu_thread: threading.Thread = None
      self.sun: sunClock = sun
      self.args = args
      # -- -- -- -- -- -- --
      self.ON_OFF_TABLE: {} = {"ON": 0, "OFF": 1}
      self.CHNL_PINS: {} = {"C1": 26, "C2": 20, "C3": 21}

   def init(self, GPIO_MODE: int = GPIO.BCM) -> bool:
      try:
         # -- -- -- -- -- -- -- --
         GPIO.setmode(GPIO_MODE)
         for p in self.CHNL_PINS.values():
            GPIO.setup(p, GPIO.OUT)
            GPIO.output(p, self.ON_OFF_TABLE["OFF"])
         # -- -- -- -- -- -- -- --
         if not self.red.ping():
            raise Exception("NoRedPong")
         # -- -- -- -- -- -- -- --
         hn: str = os.uname()[1]
         ip: str = utils.lan_ip()
         dts: str = utils.dts_utc(with_tz=True)
         redis_patt: str = f"{self.board_id}*"
         self.red.select(redisDBIdx.DB_IDX_GPIO.value)
         key: str = f"BOARD_{self.board_id}"
         self.red.delete(key)
         self.red.hset(key, mapping={"HOST": hn, "IP": ip
            , "REDIS_TRIGGER_PATT": redis_patt, "DTS": dts})
         # -- -- -- -- -- -- -- --
         redis_patt: str = f"{self.board_id}*"
         self.red_sub.psubscribe(**{redis_patt: self.__on_redis_msg__})
         self.red_sbu_thread: threading.Thread = \
            self.red_sub.run_in_thread(sleep_time=0.001)
         self.red_sbu_thread.name = self.id
         return True
      except Exception as e:
         print(e)
         return False

   def __str__(self):
      return "waveshare3chHat ver: 001"

   # -- -- -- -- -- -- -- --
   # redis hook
   # -- -- -- -- -- -- -- --
   """
      {'type': 'pmessage', 'pattern': 'DEVLAB3RHAT*'
         , 'channel': 'DEVLAB3RHAT_GPIO_OVERRIDE', 'data': 'PIN_DEVLAB3RHAT_CH_1'}
   """
   def __on_redis_msg__(self, msg: {}):
      pmsg: redisPMsg = redisPMsg(msg)
      if pmsg.chnl == f"{self.board_id}_GPIO_CONF_CHANGE":
         self.__update_chnl_pin__(pmsg)
      else:
         pass

   # -- -- -- -- -- -- -- --
   # core code
   # -- -- -- -- -- -- -- --
   def __update_chnl_pin__(self, pmsg: redisPMsg):
      try:
         # -- -- -- --
         self.red.select(redisDBIdx.DB_IDX_GPIO.value)
         CHNL_PIN_KEY = pmsg.data.strip()
         _hash = self.red.hgetall(CHNL_PIN_KEY)
         red_hash: redisChnlPinHash = redisChnlPinHash(_hash)
         chn_pin_driver: channelPinDriver = \
            channelPinDriver(red_hash, self.sun, self.ON_OFF_TABLE["ON"])
         # -- -- -- --
         STATE: str = chn_pin_driver.get_state()
         INT_STATE: int = self.ON_OFF_TABLE[STATE]
         PIN: int = self.CHNL_PINS[f"C{red_hash.BOARD_CHANNEL}"]
         GPIO.output(PIN, INT_STATE)
         # -- -- -- --
         if GPIO.input(PIN) == INT_STATE:
            print("NEW_PIN_STATE_OK")
      except Exception as e:
         print(e)
      finally:
         pass

   # -- -- -- -- -- -- -- --
   # threading
   # -- -- -- -- -- -- -- --
   def run(self) -> None:
      self.__runtime_thread__()

   def __runtime_thread__(self):
      cnt: int = 0
      while True:
         try:
            time.sleep(2.0)
            if cnt == 10:
               print(f"__thread__ : {self}")
               cnt = 0
            # -- -- -- --
            cnt += 1
         except Exception as e:
            print(e)
