
import time, redis
import os, threading
from applib.utils import utils
from applib.datatypes import redisDBIdx, redisPMsg, redisChnlPinHash
from applib.interfaces.redisHook import redisHook
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
class waveshare3chHat(redisHook, rpiHatBoard, threading.Thread):

   ACTIVE_STATE: int = 0
   ON_OFF_TABLE: {} = {"ON": 0, "OFF": 1}
   CHNL_PINS: {} = {"C1": 26, "C2": 20, "C3": 21}

   def __init__(self, xml_id: str
         , red: redis.Redis
         , sun: sunClock
         , args: object):
      # -- -- -- -- -- -- --
      threading.Thread.__init__(self)
      super().__init__()
      self.xml_id = xml_id
      self.board_id = self.xml_id.upper()
      self.red: redis.Redis = red
      self.red_sub = self.red.pubsub()
      self.red_sbu_thread: threading.Thread = None
      self.sun: sunClock = sun
      self.args = args
      # -- -- -- -- -- -- --
      # self.ON_OFF_TABLE: {} = {"ON": 0, "OFF": 1}
      # self.CHNL_PINS: {} = {"C1": 26, "C2": 20, "C3": 21}

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
         self.red_sub.psubscribe(**{redis_patt: self.redhook_on_msg})
         self.red_sbu_thread: threading.Thread = \
            self.red_sub.run_in_thread(sleep_time=0.001)
         self.red_sbu_thread.name = self.xml_id
         if not self.red_sbu_thread.is_alive():
            self.red_sbu_thread.start()
         return True
      except Exception as e:
         print(e)
         return False

   def __str__(self):
      return "waveshare3chHat ver: 001"

   # -- -- -- -- -- -- -- --
   # redis hook
   # -- -- -- -- -- -- -- --
   def redhook_on_msg(self, msg: {}):
      try:
         pmsg: redisPMsg = redisPMsg(msg)
         if pmsg.chnl == f"{self.board_id}_GPIO_CONF_CHANGE":
            self.redhook_process_msg(pmsg)
         else:
            pass
      except Exception as e:
         print(e)

   def redhook_process_msg(self, redMsg: redisPMsg):
      self.__update_chnl_pin__(redMsg)

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

   def __update_redis__(self):
      upds: [] = []
      for pk in waveshare3chHat.CHNL_PINS.keys():
         try:
            chn_id: str = pk.replace("C", "")
            PIN: int = waveshare3chHat.CHNL_PINS[pk]
            pv: int = int(GPIO.input(PIN))
            RED_PIN_KEY: str = utils.pin_redis_key(self.board_id, chn_id)
            ST: str = f"ON:{pv}" if pv == waveshare3chHat.ACTIVE_STATE else f"OFF:{pv}"
            d: {} = {"PIN": f"{pk}:{PIN}", "LAST_STATE": ST
               , "PIN_ACTIVE_STATE": waveshare3chHat.ACTIVE_STATE
               , "LAST_STATE_READ_DTS": utils.dts_utc(with_tz=True)}
            self.red.select(redisDBIdx.DB_IDX_GPIO.value)
            rv = self.red.hset(RED_PIN_KEY, mapping=d)
            upds.append(rv)
         except Exception as e:
            print(e)
      # -- -- -- --
      buff = ", ".join([str(x) for x in upds])
      print(f"[ {self.board_id} => redis updates: {buff} ]")
      # -- -- -- --

   def __refresh_channel__(self):
      # update board pin states
      def _on_each(pk):
         try:
            chn_id: str = pk.replace("C", "")
            PIN: int = waveshare3chHat.CHNL_PINS[pk]
            RED_PIN_KEY: str = utils.pin_redis_key(self.board_id, chn_id)
            self.red.select(redisDBIdx.DB_IDX_GPIO.value)
            _hash = self.red.hgetall(RED_PIN_KEY)
            red_hash: redisChnlPinHash = redisChnlPinHash(_hash)
            chn_pin_driver: channelPinDriver = \
               channelPinDriver(red_hash, self.sun, self.ON_OFF_TABLE["ON"])
            # -- -- -- --
            STATE: str = chn_pin_driver.get_state()
            NEW_INT_STATE: int = self.ON_OFF_TABLE[STATE]
            PIN: int = self.CHNL_PINS[f"C{red_hash.BOARD_CHANNEL}"]
            CURR_STATE = int(GPIO.input(PIN))
            if CURR_STATE == NEW_INT_STATE:
               print(f"NO_STATE_UPDATED_NEEDED:: CS - {CURR_STATE} : NIT - {NEW_INT_STATE}")
               return
            GPIO.output(PIN, NEW_INT_STATE)
            # -- -- -- --
            if GPIO.input(PIN) == NEW_INT_STATE:
               print(f"NEW_PIN_STATE_OK: {NEW_INT_STATE}")
         except Exception as e:
            print(e)
      # -- -- -- --
      for _pk in waveshare3chHat.CHNL_PINS.keys():
        _on_each(_pk)

   def __runtime_thread__(self):
      cnt: int = 0
      while True:
         try:
            time.sleep(4.0)
            if cnt % 4 == 0:
               self.__refresh_channel__()
            if cnt == 8:
               print(f"[ board_thread : {self} ]")
               self.__update_redis__()
               cnt = 0
            # -- -- -- --
            cnt += 1
         except Exception as e:
            print(e)
            time.sleep(16.0)
