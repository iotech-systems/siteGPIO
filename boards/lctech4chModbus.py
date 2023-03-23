
import threading, time, redis
from crcmod.predefined import *
import serial, xml.etree.ElementTree as _et
from applib.interfaces.modbusBoard import modbusBoard


class lctech4chModbus(modbusBoard, threading.Thread):

   baudrates = {4800: 0x02, 9600: 0x03, 19200: 0x04}

   def __init__(self, xid: str, red: redis.Redis, args: object):
      threading.Thread.__init__(self)
      super().__init__(args=args)
      self.id = xid
      self.red: redis.Redis = red
      self.red_sub = self.red.pubsub()
      self.args = args
      ser_port: serial.Serial = serial.Serial()
      modbus_adr: int = 0

   def init(self):
      pass

   def set_channel(self, chnl: int, val: bool):
      data = self.__set_channel_buff__(chnl, val)
      outbuff = lctech4chModbus.__crc_data__(data)
      super().__send__(outbuff)
      resp: bytearray = super().__read__()
      if resp == outbuff:
         print("\t\t[ set_channel: OK ]")

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
         outbuff = lctech4chModbus.__crc_data__(bytearray(data))
      else:
         data: [] = [0x00, 0x0f, 0x00, 0x00, 0x00, 0x08, 0x01, 0x00]
         data[0] = self.modbus_adr
         outbuff = lctech4chModbus.__crc_data__(bytearray(data))
      # -- send & recv --
      super().__send__(outbuff)
      resp: bytearray = super().__read__()

   def read_channel(self, chnl: int):
      pass

   def set_bus_address(self, old_adr: int, new_adr: int):
      """
         Set the device address to 1
            00 10 00 00 00 01 02 00 01 6A 00
         Set the device address to 255
            00 10 00 00 00 01 02 00 FF EB 80
         The 9th byte of the sending frame, 0xFF, is the written device address
      """
      self.modbus_adr = new_adr
      data: () = (0x00, 0x10, 0x00, 0x00, 0x00, 0x01, 0x02, 0x00)
      buff: bytearray = bytearray(data)
      buff.append(self.modbus_adr)
      outbuff: bytearray = lctech4chModbus.__crc_data__(buff)
      cnt_out: int = self.__send__(outbuff)
      inbuff: bytearray = self.__read__()
      return len(inbuff) == cnt_out

   def read_bus_address(self, old_adr: int):
      pass

   """
      Read the baud rate
      send: FF 03 03 E8 00 01 11 A4
      return : FF 03 02 00 04 90 53
      remarks：The 5th byte of the Return frame represent read 
      baud rate, 0x02, 0x03, x04 represents 4800, 9600, 19200.
      ping is done by getting baudrate from the board
   """
   @staticmethod
   def ping(ser, modbus_adr):
      data: [] = [0xff, 0x03, 0x03, 0xe8, 0x00, 0x01]
      data[0] = modbus_adr
      outbuff = lctech4chModbus.__crc_data__(bytearray(data))
      mb: modbusBoard = modbusBoard(ser, modbus_adr)
      mb.__send__(outbuff)
      resp: bytearray = mb.__read__()
      bdr_code = lctech4chModbus.baudrates[ser.baudrate]
      if (len(resp) > 6) and (resp[4] == bdr_code):
         rval, msg = True, f"GOOD_PONG ON: {ser.port}"
      else:
         rval, msg = False, "BAD_PONG"
      # -- end --
      print(msg)
      return rval

   def __set_channel_buff__(self, relay: int, val: bool) -> [None, bytearray]:
      """
         (0xff, 0x05, 0x00, 0x00, 0xFF, 0x00)
      """
      buff: bytearray = bytearray()
      # -- modbus address --
      buff.append(self.modbus_adr)
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
   def __crc_data__(data: bytearray):
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

   def __runtime_thread__(self):
      while True:
         time.sleep(2.0)
         print(f"__thread__ : {self}")
