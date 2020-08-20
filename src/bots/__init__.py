def start(name):
  if name == "toplane":
    from .toplane  import client
    client.main()
  elif name == "jungler":
    from .jungler  import client
    client.main()
  elif name == "midlane":
    from .midlane  import client
    client.main()
  elif name == "botlane":
    from .botlane  import client
    client.main()
  elif name == "support":
    from .support  import client
    client.main()
  elif name == "summoner":
    from .summoner import start
    start()
  elif name == "timer":
    from .timer    import start
    start()
  elif name == "neutrino":
    from .neutrino import start
    start()
  else:
    print("?")
    return