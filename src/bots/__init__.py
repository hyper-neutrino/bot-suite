def start(name):
  if name == "toplane":
    from .toplane  import client
  elif name == "jungler":
    from .jungler  import client
  elif name == "midlane":
    from .midlane  import client
  elif name == "botlane":
    from .botlane  import client
  elif name == "support":
    from .support  import client
  elif name == "summoner":
    from .summoner import start
    start()
    return
  elif name == "timer":
    from .timer    import client
  elif name == "neutrino":
    from .neutrino import client
  elif name == "testing":
    from .testing  import client
  else:
    print(f"bot {name} => ?")
    return
  client.main()