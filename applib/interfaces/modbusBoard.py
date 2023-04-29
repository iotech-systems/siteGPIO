
import abc, time, serial
from serial import Serial

class modbusBoard(object):

   readDelay = 0.200

   def __init__(self, **kwargs):
      self.args = kwargs["args"]

   def __comm_port__(self) -> Serial:
      if not self.ser_port.isOpen():
         self.ser_port.open()
      return self.ser_port

   def __send__(self, outbuff: bytearray) -> int:
      try:
         ser: serial.Serial = self.__comm_port__()
         print(f" <<< SENDING: {outbuff}")
         cnt = ser.write(outbuff)
         ser.flush()
         # -- sleep 20 ms --
         time.sleep(0.02)
         return cnt
      except Exception as e:
         print(e)
         return 0

   def __send_ser__(self, ser: serial.Serial, outbuff: bytearray):
      self.ser_port = ser
      self.__send__(outbuff)

   def __read__(self) -> [None, bytearray]:
      try:
         ser: serial.Serial = self.__comm_port__()
         ser.timeout = modbusBoard.readDelay
         inbuff: bytearray = bytearray()
         while True:
            inbuff.extend(ser.read(1))
            if ser.in_waiting == 0:
               break
         print(f" >>> RESP: {inbuff}")
         # -- return --
         return inbuff
      except Exception as e:
         print(e)
         return None
