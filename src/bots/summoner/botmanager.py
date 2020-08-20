import subprocess, sys

from utils.errors import BotError

bots = {}

aliases = {
  "toplane": "toplane",
  "top": "toplane",
  "midlane": "midlane",
  "mid": "midlane",
  "jungler": "jungler",
  "jg": "jungler",
  "jungle": "jungler",
  "botlane": "botlane",
  "bot": "botlane",
  "support": "support",
  "sup": "support",
  "timer": "timer",
  "neutrino": "neutrino"
}

titles = {
  "toplane": "TopLane",
  "jungler": "Jungler",
  "midlane": "MidLane",
  "botlane": "BotLane",
  "support": "Support",
  "timer": "Debate Timer",
  "neutrino": "Neutrino's Bot"
}

commands = {
  "toplane": ["python3", "src/main.py", "toplane"],
  "jungler": ["python3", "src/main.py", "jungler"],
  "midlane": ["python3", "src/main.py", "midlane"],
  "botlane": ["nodejs", "src/botlane.js"],
  "support": ["python3", "src/main.py", "support"],
  "timer": ["python3", "src/main.py", "timer"],
  "neutrino": ["python3", "src/main.py", "neutrino"],
}

def start(name):
  if name in aliases:
    botname = aliases[name]
    if botname in bots:
      raise BotError("{title} is already running!".format(title = titles[botname]))
    bots[botname] = subprocess.Popen(commands[botname], stdin = subprocess.PIPE, stdout = sys.stdout, stderr = sys.stderr)
    return "success"
  raise BotError("'{name}' is not a recognized bot name!".format(name = name))

def stop(name):
  if name in aliases:
    botname = aliases[name]
    if botname not in bots:
      raise BotError("{title} is not running!".format(title = titles[botname]))
    bots[botname].kill()
    del bots[botname]
    return "success"
  raise BotError("'{name}' is not a recognized bot name!".format(name = name))