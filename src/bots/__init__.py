def start(name):
  if name == "toplane":
    from .toplane  import start
    start()
  elif name == "jungler":
    from .jungler  import start
    start()
  elif name == "midlane":
    from .midlane  import start
    start()
  elif name == "botlane":
    from .botlane  import start
    start()
  elif name == "support":
    from .support  import start
    start()
  elif name == "summoner":
    from .summoner import start
    start()
  elif name == "timer":
    from .timer    import start
    start()
  elif name == "neutrino":
    from .neutrino import start
    start()
  elif name == "testing":
    from .testing  import start
  else:
    print("?")
    return