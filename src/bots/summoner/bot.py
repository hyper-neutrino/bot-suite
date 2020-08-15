import discord

from .botmanager import start, stop, aliases, titles

from utils.datautils import add_guild, load_data, save_data, setup_data
from utils.discordbot import BotClient, send

data = None
client = None

async def announce(*args, **kwargs):
  if data is None:
    raise RuntimeError("Data was not loaded yet.")
  if client is None:
    raise RuntimeError("Client is not initialized yet.")
  
  for gid in data["guilds"]:
    for cid in data["guilds"][gid]["statreports"]:
      await client.get_guild(gid).get_channel(cid).send(*args, **kwargs)

class SummonerClient(BotClient):
  def __init__(self):
    BotClient.__init__(self)
    self.name = "summoner"

  async def on_ready(self):
    global data
    
    data = load_data()
    setup_data(data, self.guilds)
    save_data(data)
    
    await announce("Summoner is now online! The rest of the team should be here soon.")
    
    start("toplane")
    start("jungler")
    start("midlane")
    start("botlane")
    start("support")
    
  async def on_guild_join(self, guild):
    add_guild(data, guild)
    save_data(data)

client = SummonerClient()

@client.command("", ["help"], "", "")
async def command_help(command, message):
  await send(message, embed = discord.Embed(
    title = "BotSuite help",
    description = """`pls help <toplane | jungler | midlane | botlane | support | summoner >`: help about a specific bot"""
  ), reaction = "check")

@client.command("Testing Commands", ["test"], "test", "Test the Summoner bot")
async def command_test(command, message):
  await send(message, "Test success!", reaction = "check")

@client.command("Bot Manager Commands", ["statwatch"], "statwatch", "watch bot status reports in this channel")
async def command_statwatch(command, message):
  data["guilds"][message.guild.id]["statreports"].add(message.channel.id)
  save_data(data)
  await send(message, "Now watching bot status reports in this channel!", reaction = "check")

@client.command("Bot Manager Commands", ["statwatch"], "statunwatch", "stop watching bot status reports in this channel")
async def command_statwatch(command, message):
  data["guilds"][message.guild.id]["statreports"] -= {message.channel.id}
  save_data(data)
  await send(message, "No longer watching bot status reports in this channel!", reaction = "check")

@client.command("Bot Manager Commands", ["stop", "\\w+"], "stop <botname | all>", "stop a certain bot or all bots")
async def command_stop(command, message):
  if command[1] == "all":
    for bot in ["toplane", "jungler", "midlane", "botlane", "support"]:
      try:
        stop(bot)
      except:
        pass
    await send(message, "All bots have been killed!")
  else:
    stop(command[1])
    await send(message, "{title} has been killed!".format(title = titles[aliases[command[1]]]))

@client.command("Bot Manager Commands", ["start", "\\w+"], "start <botname | all>", "start a certain bot or all bots")
async def command_stop(command, message):
  if command[1] == "all":
    for bot in ["toplane", "jungler", "midlane", "botlane", "support"]:
      try:
        start(bot)
      except:
        pass
    await send(message, "All bots are being started!")
  else:
    start(command[1])
    await send(message, "{title} is being started!".format(title = titles[aliases[command[1]]]))