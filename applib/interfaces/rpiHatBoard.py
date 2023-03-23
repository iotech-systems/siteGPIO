

class rpiHatBoard(object):

   readDelay = 0.200

   def __init__(self, **kwargs):
      pass

   def init(self, GPIO_MODE: int):
      pass

   def set_channel(self, chnl: int, val: bool):
      pass

   def read_channel(self, chnl: int):
      pass

   def set_bus_address(self, old_adr: int, new_adr: int):
      pass

   def read_bus_address(self, old_adr: int):
      pass

   # -- bot info --
   def get_state(self) -> object:
      pass

   def __read__(self) -> [None, bytearray]:
      pass
