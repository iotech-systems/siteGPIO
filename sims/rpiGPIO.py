

PIN_BAG = {}


class GPIO(object):

   BCM = 11
   BOARD = 10
   BOTH = 33
   FALLING = 32
   HARD_PWM = 43
   HIGH = 1
   I2C = 42
   IN = 1
   LOW = 0
   OUT = 0
   PUD_DOWN = 21
   PUD_OFF = 20
   PUD_UP = 22
   RISING = 31
   RPI_INFO = {"MANUFACTURER": "Sony", "P1_REVISION": 3, "PROCESSOR": "BC"}
   RPI_REVISION = 3
   SERIAL = 40
   SPI = 41
   UNKNOWN = -1
   VERSION = '0.7.0'

   @staticmethod
   def setmode(mode: int):
      print(["gpio.mode", mode])

   @staticmethod
   def setup(pinid: int, mode: int):
      print(["gpio.setup", pinid, mode])

   @staticmethod
   def input(pin: int) -> bool:
      return bool(PIN_BAG[pin])

   @staticmethod
   def output(pin: int, val: int):
      PIN_BAG[pin] = bool(val)
      print(PIN_BAG)

   @staticmethod
   def setwarnings(flag: bool):
      pass
