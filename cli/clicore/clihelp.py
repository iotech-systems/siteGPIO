
import os, sys
import argparse as _ap
os.chdir("../")
sys.path.insert(0, os.getcwd())
os.chdir("cli")
from boards.lctech import lct4chModbus
from boards.waveshare import wsh3chHat, wsh8chExpBoard

# -- -- -- load system boards -- -- --
SYS_BOARDS = (lct4chModbus, wsh3chHat, wsh8chExpBoard)
SYS_MM = """\n\n
   # -- -- [ xgpio menu ] -- --
     1. load system GPIO board
     2. ---
   # -- -- -- -- -- -- -- --
     0. main menu
"""


HELP_PARSER = _ap.ArgumentParser(description="Process some integers.")
HELP_PARSER.add_argument("integers", metavar="N", type=int, nargs="+",
   help="an integer for the accumulator")
HELP_PARSER.add_argument("--sum", dest="accumulate", action="store_const",
   const=sum, default=max, help="sum the integers (default: find the max)")
# -- -- -- --
# args = HELP_PARSER.parse_args()
