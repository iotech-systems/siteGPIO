import os
import time

import serial, threading
from applib.datatypes import COMMOptTimeout


class commPort(serial.Serial):

   def __init__(self, dev: str
         , baud: int
         , bsize: int
         , sbits: int
         , parity: str):
      # -- call super --
      super().__init__(port=dev, baudrate=baud, bytesize=bsize, stopbits=sbits, parity=parity)
      self.recv_buff: bytearray = bytearray()
      self.last_exception: Exception = None

   def init(self):
      try:
         if not self.is_open:
            self.open()
      except serial.SerialException as se:
         print(se)

   def send_receive(self, bbuff: bytearray) -> int:
      t = os.getenv("GPIO_BOARD_SERIAL_DELAY")
      POST_WRITE_DELAY: float = float(t) if (t not in [None, ""]) else 0.020
      try:
         print(f"\tSENT: {bbuff} -> ", end="")
         count = self.write(bbuff)
         self.flush()
         print(f"POST_WRITE_DELAY: {POST_WRITE_DELAY}")
         time.sleep(POST_WRITE_DELAY)
         if count != len(bbuff):
            raise Exception("BadSendByteCount")
         print("SENT_OK")
         if self.__receive__():
            return 0
         else:
            return 1
      except Exception as e:
         self.last_exception = e
         return 21   # exception

   def __receive__(self) -> bool:
      try:
         cnt: int = 0
         self.timeout = 0.04
         self.recv_buff.clear()
         while True:
            self.recv_buff.extend(self.read(1))
            if self.in_waiting == 0:
               cnt += 1
               if cnt <= 12:
                  continue
               else:
                  break
         # -- -- -- --
         print(f"\tRECV: {self.recv_buff} -> OK")
         # -- -- -- --
         return True
      except Exception as e:
         print(e)
