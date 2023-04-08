
from crcmod.predefined import *
import os, threading, time, redis
import serial, xml.etree.ElementTree as _et
from applib.datatypes import redisDBIdx, redisPMsg, redisChnlPinHash
from applib.interfaces.redisHook import redisHook
from applib.interfaces.modbusBoard import modbusBoard
from applib.sunclock import sunClock
from applib.utils import utils
from applib.datatypes import commArgs
from applib.commPort import commPort
from boards.buses.modbusBUS import modbusBUS


class lctech4chModbus(redisHook, modbusBoard, threading.Thread):

   BAUDRATES = {4800: 0x02, 9600: 0x03, 19200: 0x04}
   ACTIVE_STATE: int = 1
   ON_OFF_TABLE: {} = {"ON": 1, "OFF": 0}
   CHNL_PINS: {} = {"CH1": 0, "CH2": 1, "CH3": 2, "CH4": 3}

   def __init__(self, xml_id: str
         , red: redis.Redis = None
         , sun: sunClock = None
         , args: object = None):
      # -- -- -- --
      threading.Thread.__init__(self)
      super().__init__(args=args)
      self.xml_id = xml_id
      self.board_id = self.xml_id.upper()
      self.red: redis.Redis = red
      self.red_sub = None
      if self.red is not None:
         self.red_sub = self.red.pubsub()
      self.sun: sunClock = sun
      self.args = args
      # -- -- -- --
      self.comm_args: commArgs = commArgs(str(self.args))
      if not self.comm_args.parseOK:
         pass
      self.red_sbu_thread: threading.Thread = None
      self.bus_adr: int = self.comm_args.bus_adr
      # -- 9600,8,1,N --
      br, bts, sbt, par = self.comm_args.comm_info()
      # self.comm_port: serial.Serial = \
      # serial.Serial(baudrate=int(br), parity=par, stopbits=int(sbt))
      # -- -- -- --
      self.comm_port: commPort = \
         commPort(dev=self.comm_args.dev, baud=int(br), bsize=int(bts), sbits=int(sbt), parity=par)
      # -- -- -- --

   def init(self):
      try:
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
      print(redMsg)

   def __update_redis__(self):
      upds: [] = []
      def _oneach(pk):
         try:
            chn_id: str = "".join([c for c in pk if c.isdigit()])
            PIN: int = lctech4chModbus.CHNL_PINS[pk]
            PIN_VAL: int = self.read_channel(PIN)
            RED_PIN_KEY: str = utils.pin_redis_key(self.board_id, chn_id)
            ST: str = f"ON:{PIN_VAL}" if PIN_VAL == lctech4chModbus.ACTIVE_STATE else f"OFF:{PIN_VAL}"
            d: {} = {"PIN": f"{pk}:{PIN_VAL}", "LAST_STATE": ST
               , "PIN_ACTIVE_STATE": lctech4chModbus.ACTIVE_STATE
               , "LAST_STATE_READ_DTS": utils.dts_utc(with_tz=True)}
            self.red.select(redisDBIdx.DB_IDX_GPIO.value)
            rv = self.red.hset(RED_PIN_KEY, mapping=d)
            upds.append(rv)
         except Exception as e:
            print(e)
      # -- -- -- --
      for _pk in lctech4chModbus.CHNL_PINS.keys():
         _oneach(_pk)
      # -- -- -- --
      buff = ", ".join([str(x) for x in upds])
      print(f"[ {self.board_id} => redis updates: {buff} ]")
      # -- -- -- --

   def set_channel(self, chnl: int, val: bool):
      print(f"\n\t[ set_channel: ({chnl}, {val}) ]")
      # -- -- -- -- -- -- -- --
      def on_0x0(dsent: bytearray) -> bool:
         bval: bool = (dsent == self.comm_port.recv_buff)
         msg: str = "\t\tSET_OK" if bval else "\t\tSET_ERROR"
         print(msg)
         return bval
      # -- -- -- -- -- -- -- --
      # chnls come in as 1-4 by need to be moved to 0-3
      chnl = (chnl - 1)
      if chnl not in range(0, 4):
         print(f"BadChnlID: {chnl}")
         return
      data = self.__set_channel_buff__(chnl, val)
      outbuff = lctech4chModbus.crc_data(data)
      # -- -- -- -- -- -- -- --
      for idx in range(0, 1):
         print(f"\t-- SET TRY IDX: {idx}")
         rval: int = self.comm_port.send_receive(bbuff=outbuff)
         if rval == 0 and on_0x0(data):
            break
         else:
            print(f"retrying set: {idx}")
            time.sleep(0.2)
            continue
      # -- -- -- -- -- -- -- --

   def set_all_channels(self, val: bool):
      """
         5, turn on all relay
         send :FF 0F 00 00 00 08 01 FF 30 1D
         return :FF 0F 00 00 00 08 41 D3
         6,turn off all relay
         send:FF 0F 00 00 00 08 01 00 70 5D
         return :FF 0F 00 00 00 08 41 D3
      """
      if val:
         data: [] = [0x00, 0x0f, 0x00, 0x00, 0x00, 0x08, 0x01, 0xff]
         data[0] = self.modbus_adr
         outbuff = lctech4chModbus.crc_data(bytearray(data))
      else:
         data: [] = [0x00, 0x0f, 0x00, 0x00, 0x00, 0x08, 0x01, 0x00]
         data[0] = self.modbus_adr
         outbuff = lctech4chModbus.crc_data(bytearray(data))
      # -- send & recv --
      super().__send__(outbuff)
      resp: bytearray = super().__read__()

   def read_channel(self, chnl: int):
      pass

   def write_channel(self, chnl: int, val: int) -> int:
      pass

   def set_bus_address(self, old_adr: int, new_adr: int):
      """
         Set the device address to 1
            00 10 00 00 00 01 02 00 01 6A 00
         Set the device address to 255
            00 10 00 00 00 01 02 00 FF EB 80
         The 9th byte of the sending frame, 0xFF, is the written device address
      """
      # data: () = (0x00, 0x10, 0x00, 0x00, 0x00, 0x01, 0x02, 0x00)
      # buff: bytearray = bytearray(data)
      # buff.append(self.modbus_adr)
      # outbuff: bytearray = lctech4chModbus.crc_data(buff)
      # cnt_out: int = self.__send__(outbuff)
      # inbuff: bytearray = self.__read__()
      # return len(inbuff) == cnt_out
      pass

   """
      10,read device address
      send   : FF 01 00 00 00 08 28 12
      return : FF 01 01 01 A1 A0
   """
   def read_bus_address(self):
      print("[ read_bus_address ]")
      # FF 01 00 00 00 08
      data: [] = [None, 0x01, 0x00, 0x00, 0x00, 0x08]
      data[0] = self.bus_adr
      outbuff = lctech4chModbus.crc_data(bytearray(data))
      snd_recv_val = self.comm_port.send_receive(outbuff)
      print(snd_recv_val)

   """
      15,Read the baud rate
         send   : FF 03 03 E8 00 01 11 A4
         return : FF 03 02 00 04 90 53
      remarks：The 5th byte of the Return 
         frame represent read baud rate, 0x02, 0x03, x04 represents 4800,9600,19200.
   """
   def ping(self):
      print("\n\t[ ping ]")
      def __on_0(dsent: bytearray):
         if self.comm_port.recv_buff[0:1] == dsent[0:1]:
            print("\tGOOD_PONG")
         else:
            print("\tNO_PONG")
      # -- -- -- --
      # 00 03 00 00 00 01 85 DB
      data: [] = [None, 0x03, 0x03, 0xE8, 0x00, 0x01]
      data[0] = self.bus_adr
      outbuff = lctech4chModbus.crc_data(bytearray(data))
      snd_recv_code = self.comm_port.send_receive(bbuff=outbuff)
      if snd_recv_code == 0:
         __on_0(outbuff)
      else:
         pass

   def __set_channel_buff__(self, relay: int
         , val: bool) -> [None, bytearray]:
      """
         (0xff, 0x05, 0x00, 0x00, 0xFF, 0x00)
      """
      buff: bytearray = bytearray()
      # -- modbus address --
      buff.append(self.bus_adr)
      # -- modbus function --
      buff.append(0x05)
      # -- relay address --
      buff.extend([0, relay])
      if val:
         buff.extend([0xff, 0x00])
      else:
         buff.extend([0x00, 0x00])
      # -- return buffer --
      return buff

   @staticmethod
   def crc_data(data: bytearray):
      crc_func = mkPredefinedCrcFun("modbus")
      crc_int = crc_func(data)
      crc = crc_int.to_bytes(2, "little")
      data.extend(crc)
      return data

   def __str__(self):
      return "lctech4chModbus ver. 001"

   # -- -- -- -- -- -- -- -- -- -- -- --
   # threading
   # -- -- -- -- -- -- -- -- -- -- -- --
   def run(self) -> None:
      self.__runtime_thread__()

   def __refresh_channel__(self):
      pass

   def __runtime_thread__(self):
      cnt: int = 0
      # -- -- -- --
      def __loop():
         nonlocal cnt
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
      # -- -- -- --
      while True:
         __loop()
      # -- -- -- --
