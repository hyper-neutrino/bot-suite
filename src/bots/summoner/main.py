import asyncio, pickle, traceback

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

async def discord():
  await client.start(config["discord-tokens"]["summoner"])

async def direct():
  gid = 699314655973212242
  cid = 741144497588535378
  while True:
    try:
      bot, message = (await ainput(">>> ")).split(maxsplit = 1)
      if bot == "gg":
        if message.strip().isdigit():
          g = int(message.strip())
          if client.get_guild(g):
            gid = g
            print("Set guild to {guild}!".format(guild = client.get_guild(gid).name))
          else:
            print("Guild does not exist, or bot is not in that guild!")
        else:
          for guild in client.guilds:
            if guild.name == message.strip():
              gid = guild.id
              print("Set guild to {guild}!".format(guild = guild.name))
              break
          else:
            print("Guild does not exist, or bot is not in that guild!")
      elif bot == "gc":
        if message.strip().isdigit():
          c = int(message.strip())
          if client.get_guild(gid).get_channel(c):
            cid = c
            print("Set channel to {guild}#{channel}!".format(guild = client.get_guild(gid).name, channel = client.get_guild(gid).get_channel(cid).name))
          else:
            print("Channel does not exist, or bot does not have access!")
        else:
          for channel in client.get_guild(gid).channels:
            if channel.name == message.strip():
              cid = channel.id
              print("Set channel to {channel}!".format(channel = channel.name))
              break
          else:
            print("Channel does not exist, or bot does not have access!")
      elif bot == "send":
        if gid == -1 or cid == -1:
          print("Guild or channel not set!")
        else:
          guild = client.get_guild(gid)
          for emoji in guild.emojis:
            message = message.replace(":{name}:".format(name = emoji.name), str(emoji))
          for member in guild.members:
            message = message.replace("@[{name}]".format(name = member.display_name), member.mention).replace("@[{name}]".format(name = member.name), member.mention)
          for member in guild.members:
            message = message.replace("@{name}".format(name = member.display_name), member.mention).replace("@{name}".format(name = member.name), member.mention)
          await guild.get_channel(cid).send(message)
          print("Sent!")
    except:
      print(traceback.format_exc())

def start():
  loop = asyncio.get_event_loop()
  loop.run_until_complete(asyncio.gather(
    backup(),
    direct(),
    discord()
  ))