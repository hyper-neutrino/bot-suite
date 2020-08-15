import subprocess

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
  "sup": "support"
}

titles = {
  "toplane": "TopLane",
  "jungler": "Jungler",
  "midlane": "MidLane",
  "botlane": "BotLane",
  "support": "Support"
}

def start(name):
  if name in aliases:
    botname = aliases[name]
    if botname in bots:
      raise BotError("{title} is already running!".format(title = titles[botname]))
    bots[botname] = subprocess.Popen(["python3", "src/main.py", botname])
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