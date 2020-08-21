import asyncio, datetime, discord, json, pickle, random, traceback

from aioconsole import ainput

from .bot import client
from .botmanager import start, stop, aliases, bots

from utils.datautils import config, lock
  
async def backup():
  while True:
    with lock:
      with open("data.pickle", "rb") as f:
        data = pickle.load(f)
      if data.get("working"):
        with open("data-backup.pickle", "wb") as f:
          pickle.dump(data, f)
#         await client.announce("Data is working; saving backup now!")
      else:
        with open("data-backup.pickle", "rb") as f:
          with open("data.pickle", "wb") as g:
            g.write(f.read())
        await client.announce("Data contents are broken; retrieving from backup!")
    await asyncio.sleep(300)

async def startbot():
  await client.start(config["discord-tokens"]["summoner"])

async def direct():
  while True:
    line = await ainput(">>> ")
    for botname in bots:
      if line.startswith(botname):
        bots[botname].stdin.write(bytes(line[len(botname) + 1:] + "\n", "utf-8"))
        bots[botname].stdin.flush()
        break
    else:
      await client.dircomm(line)

async def profiles():
  while True:
    now = datetime.datetime.now()
    tmr = datetime.datetime.fromtimestamp(now.timestamp() + 60 * 60 * 24)
    nd = datetime.datetime(tmr.year, tmr.month, tmr.day)
    delay = int(nd.timestamp() - now.timestamp())
    if delay < 0: break
    print(f"Changing profile in {delay} seconds!")
    await asyncio.sleep(delay)
    profiles = random.choice(config["profile-pictures"])
    if "summoner" in profiles:
      await client.edit_pfp(profiles["summoner"])
    for name in profiles:
      if name in bots:
        bots[name].stdin.write(bytes("profilepic " + profiles[name] + "\n", "utf-8"))
        bots[name].stdin.flush()

def start():
  loop = asyncio.get_event_loop()
  loop.run_until_complete(asyncio.gather(
    startbot(),
    backup(),
    profiles(),
    direct()
  ))