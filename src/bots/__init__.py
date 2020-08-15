from .toplane import start as start_toplane
from .jungler import start as start_jungler
from .midlane import start as start_midlane
from .botlane import start as start_botlane
from .support import start as start_support
from .summoner import start as start_summoner

def start(name):
  if name == "toplane":
    start_toplane()
  elif name == "jungler":
    start_jungler()
  elif name == "midlane":
    start_midlane()
  elif name == "botlane":
    start_botlane()
  elif name == "support":
    start_support()
  elif name == "summoner":
    start_summoner()