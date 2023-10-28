
import serial, typing as t
from crcmod.predefined import *
import os, threading, time, redis
from applib.datatypes import redisDBIdx, redisPMsg, redisChnlPinHash
from applib.interfaces.redisHook import redisHook
from applib.interfaces.modbusBoard import modbusBoard
from applib.channelPinDriver import channelPinDriver
from applib.sunclock import sunClock
from applib.utils import utils
from applib.datatypes import commArgs
from applib.commPort import commPort


class lctech4chModbus(redisHook, modbusBoard, threading.Thread):

   BAUDRATES = {4800: 0x02, 9600: 0x03, 19200: 0x04}
   ACTIVE_STATE: int = 1
   ON_OFF_TABLE: {} = {"ON": 1, "OFF": 0}
   CHNL_PINS: {} = {"CH1": 0, "CH2": 1, "CH3": 2, "CH4": 3}
   PORT_LOCK = threading.Lock()

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
      self.red_sbu_thread: threading.Thread = t.Any
      self.bus_adr: int = self.comm_args.bus_adr
      self.comm_port: commPort = t.Any

   def init(self):
      try:
         # -- -- -- -- -- -- -- --
         if not os.path.exists(self.comm_args.dev):
            lctech4chModbus.try_update_dev(self)
         if not os.path.exists(self.comm_args.dev):
            raise Exception(f"UnableToFindDev: {self.comm_args.dev}")
         # -- -- -- -- -- -- -- --
         if not self.red.ping():
            raise Exception("NoRedPong")
         else:
            print(f"\n\t[ GOOD_RED_PONG ]\n")
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
         print(f"RedisSubscribingTo: {redis_patt}")
         self.red_sub.psubscribe(**{redis_patt: self.redhook_on_msg})
         self.red_sbu_thread: threading.Thread = \
            self.red_sub.run_in_thread(sleep_time=0.01)
         self.red_sbu_thread.name = self.xml_id
         # -- -- -- -- -- -- -- --
         if not self.red_sbu_thread.is_alive():
            self.red_sbu_thread.start()
         return True
      except FileNotFoundError as e:
         # -- ttydev not foundx --
         print(e)
         return False
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
            l0 = f"  redhook_on_msg: {pmsg.chnl} "
            l1 = f"  {pmsg} "
            frm = (len(l1) - 3) * "-"
            print(f"\n\n\t[ {frm} ]")
            print(f"\t{l0}\n\t{l1}")
            print(f"\t[ {frm} ]\n\n")
            self.redhook_process_msg(pmsg)
         else:
            pass
      except Exception as e:
         print(e)

   def redhook_process_msg(self, redMsg: redisPMsg):
      """
         create serial port only when the msgs comes in
      """
      try:
         # -- load red hash --
         self.red.select(redisDBIdx.DB_IDX_GPIO.value)
         CHNL_PIN_KEY = redMsg.data.strip()
         _hash = self.red.hgetall(CHNL_PIN_KEY)
         red_hash: redisChnlPinHash = redisChnlPinHash(_hash)
         chn_pin_driver: channelPinDriver =\
            channelPinDriver(red_hash, self.sun, lctech4chModbus.ON_OFF_TABLE["ON"])
         # -- -- -- --
         br, bts, sbt, par = self.comm_args.comm_info()
         self.comm_port: commPort =\
            commPort(dev=self.comm_args.dev, baud=int(br), bsize=int(bts), sbits=int(sbt), parity=par)
         # -- -- -- --
         STATE: str = chn_pin_driver.get_state()
         INT_STATE: int = lctech4chModbus.ON_OFF_TABLE[STATE]
         PIN: int = lctech4chModbus.CHNL_PINS[f"CH{(red_hash.BOARD_CHANNEL + 1)}"]
         lctech4chModbus.set_channel_state(self, PIN, bool(INT_STATE))
      except Exception as e:
         print(f"e: {e}")
      finally:
         pass

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
      PIN: int = lctech4chModbus.CHNL_PINS[f"CH{chnl}"]
      print(f"\n\t[ set_channel: CH{chnl} - PIN {PIN} | val: {val} ]")
      # -- -- -- -- -- -- -- --
      def on_rval_0(dsent: bytearray) -> bool:
         bval: bool = (dsent == self.comm_port.recv_buff)
         msg: str = "\t\tSET_OK" if bval else "\t\tSET_ERROR"
         print(msg)
         return bval
      # -- -- -- -- -- -- -- --
      chnl = (chnl - 1)
      if chnl not in range(0, 4):
         print(f"BadChnlID: {chnl}")
         return
      data = self.__set_channel_buff__(chnl, val)
      outbuff = lctech4chModbus.crc_data(data)
      # -- -- -- -- -- -- -- --
      br, bts, sbt, par = self.comm_args.comm_info()
      self.comm_port: commPort =\
         commPort(dev=self.comm_args.dev, baud=int(br), bsize=int(bts), sbits=int(sbt), parity=par)
      # -- -- -- -- -- -- -- --
      for idx in range(0, 2):
         print(f"\t-- SET TRY IDX: {idx}")
         rval: int = self.comm_port.send_receive(bbuff=outbuff)
         if rval == 0 and on_rval_0(data):
            break
         else:
            print(f"\tretrying set: {idx}")
            time.sleep(0.2)
            continue
      # -- -- -- -- -- -- -- --

   # def set_all_channels(self, val: bool):
   #    """
   #       5, turn on all relay
   #       send :FF 0F 00 00 00 08 01 FF 30 1D
   #       return :FF 0F 00 00 00 08 41 D3
   #       6,turn off all relay
   #       send:FF 0F 00 00 00 08 01 00 70 5D
   #       return :FF 0F 00 00 00 08 41 D3
   #    """
   #    if val:
   #       data: [] = [0x00, 0x0f, 0x00, 0x00, 0x00, 0x08, 0x01, 0xff]
   #       data[0] = self.modbus_adr
   #       outbuff = lctech4chModbus.crc_data(bytearray(data))
   #    else:
   #       data: [] = [0x00, 0x0f, 0x00, 0x00, 0x00, 0x08, 0x01, 0x00]
   #       data[0] = self.modbus_adr
   #       outbuff = lctech4chModbus.crc_data(bytearray(data))
   #    # -- send & recv --
   #    super().__send__(outbuff)
   #    resp: bytearray = super().__read__()

   def read_channel(self, chnl: int) -> int:
      return 1

   def write_channel(self, chnl: int, val: int) -> int:
      return 1

   def set_bus_address(self, old_adr: int, new_adr: int):
      """ Set the device address to 1
            00 10 00 00 00 01 02 00 01 6A 00
         Set the device address to 255
            00 10 00 00 00 01 02 00 FF EB 80
         The 9th byte of the sending frame, 0xFF, is the written device address
         00 10 00 00 00 01 02 00 FF """
      data: [] = [old_adr, 0x10, 0x00, 0x00, 0x00, 0x01, 0x02, 0x00, new_adr]
      buff: bytearray = bytearray(data)
      outbuff: bytearray = lctech4chModbus.crc_data(buff)
      br, bts, sbt, par = self.comm_args.comm_info()
      self.comm_port: commPort = \
         commPort(dev=self.comm_args.dev, baud=int(br), bsize=int(bts), sbits=int(sbt), parity=par)
      rval = self.comm_port.send_receive(outbuff)
      print(f"\tRVAL: {rval}")
      if buff == self.comm_port.recv_buff:
         print(f"\tNew MODBUS address set to: {new_adr}")
      else:
         print("\tMODBUS address NOT SET!")

   """ 10,read device address
      send   : FF 01 00 00 00 08 28 12
      return : FF 01 01 01 A1 A0 """
   def read_bus_address(self):
      print("[ read_bus_address ]")
      data: [] = [None, 0x01, 0x00, 0x00, 0x00, 0x08]
      data[0] = self.bus_adr
      outbuff = lctech4chModbus.crc_data(bytearray(data))
      snd_recv_val = self.comm_port.send_receive(outbuff)
      print(snd_recv_val)

   """ 15,Read the baud rate
         send   : FF 03 03 E8 00 01 11 A4
         return : FF 03 02 00 04 90 53
      remarks：The 5th byte of the Return 
         frame represent read baud rate, 0x02, 0x03, x04 represents 4800,9600,19200. """
   def ping(self):
      # -- -- -- --
      print("\n\t[ ping ]")
      br, bts, sbt, par = self.comm_args.comm_info()
      self.comm_port: commPort = \
         commPort(dev=self.comm_args.dev, baud=int(br), bsize=int(bts), sbits=int(sbt), parity=par)
      # -- -- -- --
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
         , val: int) -> [None, bytearray]:
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
      if val == 1:
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

   @staticmethod
   def set_channel_state(_self, chnl: int, val: bool):
      lctech4chModbus.PORT_LOCK.acquire()
      comm_port: commPort = None
      int_val = 1 if val is True else 0
      try:
         PIN: int = lctech4chModbus.CHNL_PINS[f"CH{chnl}"]
         print(f"\n\t[ set_channel: CH{chnl} - PIN {PIN} | val: {int_val} ]")
         # -- -- -- -- -- -- -- --
         def on_rval_0(dsent: bytearray) -> bool:
            bval: bool = (dsent == comm_port.recv_buff)
            print("\t\tSET_OK" if bval else "\t\tSET_ERROR")
            return bval
         # -- -- -- -- -- -- -- --
         chnl = (chnl - 1)
         if chnl not in range(0, 4):
            print(f"BadChnlID: {chnl}")
            return
         data = _self.__set_channel_buff__(chnl, val)
         outbuff = lctech4chModbus.crc_data(data)
         # -- -- -- -- -- -- -- --
         print(f"[ boardID: {_self.xml_id} | dev: {_self.comm_args.dev} ]")
         br, bts, sbt, par = _self.comm_args.comm_info()
         lctech4chModbus.try_update_dev(_self)
         # -- -- -- -- -- -- -- --
         comm_port = commPort(dev=_self.comm_args.dev, baud=int(br)
            , bsize=int(bts), sbits=int(sbt), parity=par)
         if comm_port.isOpen():
            print(f"[ CommPortOpen: {comm_port.port } ]")
         # -- -- -- -- -- -- -- --
         for idx in range(0, 2):
            print(f"\t-- SET TRY IDX: {idx}")
            rval: int = comm_port.send_receive(bbuff=outbuff)
            if rval == 0 and on_rval_0(data):
               # -- --
               ST = f"ON:{int_val}" if int_val == lctech4chModbus.ACTIVE_STATE else f"OFF:{int_val}"
               d: {} = {"LAST_STATE": ST
                  , "LAST_STATE_READ_DTS": utils.dts_utc(with_tz=True)}
               # -- --
               RED_PIN_KEY: str = utils.pin_redis_key(_self.board_id, str(chnl))
               _self.red.select(redisDBIdx.DB_IDX_GPIO.value)
               rv = _self.red.hset(RED_PIN_KEY, mapping=d)
            else:
               print(f"\tretrying set: {idx}")
               time.sleep(0.2)
               continue
         # -- -- -- -- -- -- -- --
         if comm_port.isOpen():
            comm_port.close()
         # -- -- -- -- -- -- -- --
      except Exception as e:
         print(e)
      finally:
         # -- -- -- -- -- -- -- --
         if comm_port is not None and comm_port.isOpen():
            comm_port.close()
         if comm_port is not None:
            print(f"[ CommPortClosed: {comm_port.port} ]")
         # -- -- -- -- -- -- -- --
         lctech4chModbus.PORT_LOCK.release()

   @staticmethod
   def get_comm_dev(mb_adr: int, bdr: int, par: str) -> (int, str):
      # -- auto detect com port --
      print("[ get_comm_dev ]")
      ports = utils.usbPorts()
      for port in ports:
         try:
            print(f"TestingPortName: {port.name}")
            ser = serial.Serial(port.device, baudrate=bdr, parity=par)
            if lctech4chModbus.__ping(ser, mb_adr):
               print(f"\n\t[ MB_ADDRESS: {mb_adr} | ON: {port.device} ]\n")
               return 0, ser.port
            else:
               continue
         except Exception as e:
            print(e)
            return 2, "Error"
      # -- -- -- --
      return 1, "NotFound"

   @staticmethod
   def __ping(ser: serial.Serial, modbus_adr) -> (int, str):
      data: [] = [0xff, 0x03, 0x03, 0xe8, 0x00, 0x01]
      data[0] = modbus_adr
      outbuff = lctech4chModbus.crc_data(bytearray(data))
      ser.write(outbuff)
      ser.flush()
      time.sleep(0.02)
      ser.timeout = modbusBoard.readDelay
      resp: bytearray = bytearray()
      while True:
         resp.extend(ser.read(1))
         if ser.in_waiting == 0:
            break
      bdr_code = lctech4chModbus.BAUDRATES[ser.baudrate]
      if (len(resp) > 6) and (resp[4] == bdr_code):
         rval, msg = True, f"GOOD_PONG ON: {ser.port}"
      else:
         rval, msg = False, "BAD_PONG"
      # -- end --
      print(msg)
      return rval

   @staticmethod
   def try_update_dev(_self):
      print(f"[ boardID: {_self.xml_id} | dev: {_self.comm_args.dev} ]")
      br, bts, sbt, par = _self.comm_args.comm_info()
      if _self.comm_args.dev == "auto":
         err, msg_dev = lctech4chModbus.get_comm_dev(mb_adr=_self.comm_args.bus_adr, bdr=br, par=par)
         print([err, msg_dev])
         if err != 0:
            return
         _self.comm_args.dev = msg_dev

   def __str__(self):
      return "lctech4chModbus ver. 001"

   # -- -- -- -- -- -- -- -- -- -- -- --
   # threading
   # -- -- -- -- -- -- -- -- -- -- -- --
   def run(self) -> None:
      self.__runtime_thread__()

   def __refresh_channel__(self):
      def _on_each(pk):
         try:
            chn_id: str = pk.replace("CH", "")
            RED_PIN_KEY: str = utils.pin_redis_key(self.board_id, chn_id)
            self.red.select(redisDBIdx.DB_IDX_GPIO.value)
            _hash = self.red.hgetall(RED_PIN_KEY)
            red_hash: redisChnlPinHash = redisChnlPinHash(_hash)
            chn_pin_driver: channelPinDriver = \
               channelPinDriver(red_hash, self.sun, self.ON_OFF_TABLE["ON"])
            # -- -- -- --
            STATE: str = chn_pin_driver.get_state()
            NEW_INT_STATE: int = self.ON_OFF_TABLE[STATE]
            lctech4chModbus.set_channel_state(self, int(chn_id), bool(NEW_INT_STATE))
            # -- -- -- --
         except Exception as e:
            print(e)
         # -- -- -- --
      for _pk in lctech4chModbus.CHNL_PINS.keys():
         _on_each(_pk)

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
