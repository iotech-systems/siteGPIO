
import os, sys, redis
import configparser as _cp
cwd = os.getcwd()
os.chdir("../")
_p = os.getcwd()
sys.path.insert(0, _p)
from boards.lctech4chModbus import lctech4chModbus

INI: _cp.ConfigParser = _cp.ConfigParser()
INI.read("inis/dev_sitegpio.ini")

REDIS_SEC = "REDIS"
RED_HOST: str = INI.get(REDIS_SEC, "HOST")
RED_PORT: int = INI.getint(REDIS_SEC, "PORT")
RED_PWD: str = INI.get(REDIS_SEC, "PWD")
# ---  create & test  ---
RED: redis.Redis = redis.Redis(host=RED_HOST, port=RED_PORT
   , password=RED_PWD, decode_responses=True)
if not RED.ping():
   raise Exception("NoRedPong")
# -- -- -- -- -- -- -- --
print("GoodRedPong")


def main():
   lctach: lctech4chModbus = lctech4chModbus("xml_id", red=RED)


# -- -- -- -- -- -- -- -- -- -- -- --
if __name__ == "__main__":
    main()
