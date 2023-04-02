
import abc


class modbusBUS(object):

   def __init__(self, dev: str, baudrate: int, parity: str):
      self.dev = dev
      self.baudrate: int = baudrate
      self.parity = parity

   @abc.abstractmethod
   def read(self) -> int:
      pass

   @abc.abstractmethod
   def write(self) -> int:
      pass
