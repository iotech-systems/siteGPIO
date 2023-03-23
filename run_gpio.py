#!/usr/bin/env python3

import os.path, redis
import xml.etree.ElementTree as _et
import configparser as _cp
from applib.boardManager import boardManager

IOTECH_ENV: str = os.getenv("IOTECH_ENV")
if IOTECH_ENV is None:
   pass
elif IOTECH_ENV == "DEV":
   pass
else:
   pass

INI_FILE: str = "sitegpio.ini"
INI: _cp.ConfigParser = _cp.ConfigParser()
INI.read(INI_FILE)

REDIS_CONN: str = "REDIS_PROD"
if IOTECH_ENV == "DEV":
   REDIS_CONN = "REDIS_DEV"

RED_HOST: str = INI.get(REDIS_CONN, "HOST")
RED_PORT: int = INI.getint(REDIS_CONN, "PORT")
RED_PWD: str = INI.get("REDIS_CORE", "PWD")
# ---  create & test  ---
RED: redis.Redis = redis.Redis(host=RED_HOST, port=RED_PORT
   , password=RED_PWD, decode_responses=True)
if not RED.ping():
   raise Exception("NoRedPong")
# -- -- -- -- -- -- -- --

BOARDS_XML_FILE: str = INI.get("CORE", "BOARDS_XML_FILE")
if not os.path.exists(BOARDS_XML_FILE):
   raise FileNotFoundError(BOARDS_XML_FILE)
XML: _et.Element = _et.parse(BOARDS_XML_FILE).getroot()

HOSTNAME: str = os.uname()[1]
xpath = f"host[@name=\"{HOSTNAME}\"]"
HOST_XML: _et.Element = XML.find(xpath)

BOARD_MANAGER: boardManager = boardManager(ini=INI, red=RED, xml=HOST_XML)
if not BOARD_MANAGER.init():
   raise Exception("BoardManagerInitError")

if not BOARD_MANAGER.start():
   raise Exception("BoardManagerStartError")

def main():
   pass


# -- -- entry point -- --
if __name__ == "__main__":
   main()
