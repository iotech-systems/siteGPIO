
import redis
import xml.etree.ElementTree as _et
import configparser as _cp


class redisConnector(object):

   def __init__(self, ini: _cp.ConfigParser, elm: _et.Element):
      self.ini: _cp.ConfigParser = ini
      self.eml: _et.Element = elm

   def init(self):
      pass
