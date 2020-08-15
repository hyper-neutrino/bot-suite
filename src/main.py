import sys

from bots import start

start(sys.argv[1] if len(sys.argv) > 1 else "summoner")