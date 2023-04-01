
import abc
from applib.datatypes import redisPMsg

class redisHook(object):

   @abc.abstractmethod
   def redhook_on_msg(self, msg: {}):
      pass

   @abc.abstractmethod
   def redhook_process_msg(self, redMsg: redisPMsg):
      pass
