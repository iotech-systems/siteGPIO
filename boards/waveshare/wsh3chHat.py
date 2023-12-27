import gc
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

   helpinfo = """
      [ waveshare3chHat - help ]
         ACTIVE_STATE: int = 0
         ON_OFF_TABLE: {} = {"ON": 0, "OFF": 1}
         CHNL_PINS: {} = {"C1": 26, "C2": 20, "C3": 21}
   """

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
      self.red_thread_exp: bool = False

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
         self.__create_red_eventing_thread__()
         # -- -- -- -- -- -- -- --
         if not self.red_sbu_thread.is_alive():
            self.red_sbu_thread.start()
         # -- -- -- -- -- -- -- --
         return True
      except Exception as e:
         print(e)
         return False

   def __str__(self):
      return "waveshare3chHat ver: 002"

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
         # -- -- -- --
         self.red_thread_exp = False
      except Exception as e:
         print(e)
         self.red_thread_exp = True
      finally:
         pass

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
         strSTATE: str = chn_pin_driver.get_state()
         intSTATE: int = self.ON_OFF_TABLE[strSTATE]
         b_chnl: str = f"C{red_hash.BOARD_CHANNEL}"
         PIN: int = self.CHNL_PINS[b_chnl]
         # -- -- -- --
         oldSTATE: int = GPIO.input(PIN)
         if oldSTATE == intSTATE:
            print(f"\t[ wsh3chHat: {self.xml_id} | NoStateChangeNeeded ]")
            return
         # -- -- -- --
         print(f"\t[ wsh3chHat: {self.xml_id} | StateChangeNeeded ]")
         GPIO.output(PIN, intSTATE)
         state_chng: bool = (GPIO.input(PIN) == intSTATE)
         msg: str = f"\t -> STATE_CHANGE: {state_chng} | {b_chnl}" \
            f" | {oldSTATE} -> {intSTATE} | {red_hash.CHANNEL_NAME}"
         print(msg)
         # -- -- -- --
      except Exception as e:
         print(e)
      finally:
         pass

   # -- -- -- -- -- -- -- --
   # threading
   # -- -- -- -- -- -- -- --
   def run(self) -> None:
      self.__runtime_thread__()

   def __create_red_eventing_thread__(self):
      SLEEP_TIME: float = 0.200
      self.red_sbu_thread = None
      self.red_thread_exp = False
      self.red_sbu_thread: threading.Thread = \
         self.red_sub.run_in_thread(sleep_time=SLEEP_TIME, exception_handler=self.__on_red_exception__)
      self.red_sbu_thread.name = self.xml_id

   def __on_red_exception__(self, e, pubsub, src):
      try:
         print([e, pubsub, src])
         gc.collect()
         self.red_thread_exp = True
      except Exception as e:
         print(e)
      finally:
         pass

   def __check_red_thread__(self):
      if self.red_thread_exp:
         self.__create_red_eventing_thread__()
      else:
         pass

   """
      sends data to redis to update board state
   """
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
               return
            GPIO.output(PIN, NEW_INT_STATE)
            print(f"\t[ wsh3chHat: {self.xml_id} | {pk} | StateChange | {CURR_STATE} -> {NEW_INT_STATE} ]")
            # -- -- -- --
            if GPIO.input(PIN) == NEW_INT_STATE:
               pass
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
               self.__check_red_thread__()
               cnt = 0
            # -- -- -- --
            cnt += 1
         except Exception as e:
            print(e)
            time.sleep(16.0)
