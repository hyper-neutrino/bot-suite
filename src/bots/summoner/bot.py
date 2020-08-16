import datetime, discord, time

from .botmanager import start, stop, aliases, titles

from utils.datautils import config, data, save_data, default
from utils.discordbot import BotClient, send, get_member

client = None

class SummonerClient(BotClient):
  def __init__(self):
    BotClient.__init__(self)
    self.name = "summoner"

  async def on_ready(self):
    await (self.announce("Summoner is now online! Starting the other bots now."))
    
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

@client.command("Utility Commands", ["test"], "test", "Test the Summoner bot")
async def command_test(command, message):
  await send(message, "Test success!", reaction = "check")

@client.command("Utility Commands", ["ping"], "ping", "check your ping")
async def command_ping(command, message):
  await send(message, "Pong! ({ping} ms)".format(
    ping = int((time.time() - (message.created_at - datetime.datetime(1970, 1, 1)) / datetime.timedelta(seconds = 1)) * 1000)
  ), reaction = "🏓")

@client.command("Bot Manager Commands", ["statwatch"], "statwatch", "watch bot status reports in this channel")
async def command_statwatch(command, message):
  default("statreports", set()).add((message.guild.id, message.channel.id))
  save_data()
  await send(message, "Now watching bot status reports in this channel!", reaction = "check")

@client.command("Bot Manager Commands", ["statunwatch"], "statunwatch", "stop watching bot status reports in this channel")
async def command_statunwatch(command, message):
  default("statreports", set()).discard((message.guild.id, message.channel.id))
  save_data()
  await send(message, "No longer watching bot status reports in this channel!", reaction = "check")

@client.command("Bot Manager Commands", ["stop", ".+"], "stop <botname | all>", "stop a certain bot or all bots")
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

@client.command("Bot Manager Commands", ["start", ".+"], "start <botname | all>", "start a certain bot or all bots")
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

@client.command("Bot Manager Commands", ["restart", ".+"], "restart <botname | all>", "restart a certain bot or all bots (functionally `stop` + `start`)")
async def command_restart(command, message):
  if command[1] == "all":
    for bot in ["toplane", "jungler", "midlane", "botlane", "support"]:
      try:
        stop(bot)
        start(bot)
      except:
        pass
    await send(message, "All bots are being restarted!")
  else:
    stop(command[1])
    start(command[1])
    await send(message, "{title} is being restarted!".format(title = titles[aliases[command[1]]]))

@client.command("Bot Manager Commands", ["bonk", ".+", "?"], "bonk <user> [time]", "alias for `ignore`")
@client.command("Bot Manager Commands", ["ignore", ".+", "?"], "ignore <user> [time]", "ignore a user until [time] seconds from now")
async def command_ignore(command, message):
  if len(command) > 2 and not command[2].isdigit():
    await send(message, "Invalid time! Must be an integer.", reaction = "x")
  else:
    member = await get_member(message.guild, command[1], message.author)
    if member == message.author:
      await send(message, "You cannot {verb} yourself!".format(verb = command[0]))
    elif member.id in config["global-arguments"]["sudo"]:
      await send(message, "You cannot {verb} {name} as they are a sudo user!".format(verb = command[0], name = member.display_name))
    else:
      default("ignore", {})[(message.guild.id, member.id)] = time.time() + int(command[2]) if len(command) > 2 else -1
      save_data()
      if len(command) > 2:
        await send(message, ("Bonk! " if command[0] == "bonk" else "") + "{mention} is being ignored for {time} second{plural}!".format(
          mention = member.mention,
          time = command[2],
          plural = "" if command[2] == "1" else "s"
        ))
      else:
        await send(message, ("Bonk! " if command[0] == "bonk" else "") + "{mention} is being ignored indefinitely!".format(mention = member.mention))

@client.command("Bot Manager Commands", ["unbonk", ".+", "?"], "unbonk <user>", "alias for `unignore`")
@client.command("Bot Manager Commands", ["unignore", ".+", "?"], "unignore <user>", "stop ignoring a user immediately (essentially `ignore <user> 0`)")
async def command_unignore(command, message):
  member = await get_member(message.guild, command[1], message.author)
  if member == message.author:
    await send(message, "If you were ignored, you would not be able to unignore yourself. Since you aren't, this command doesn't change anything. Please reconsider your choices.", reaction = "x")
  else:
    key = (message.guild.id, member.id)
    if key in default("ignore", {}) and (data()["ignore"][key] == -1 or data()["ignore"][key] > time.time()):
      del data()["ignore"][key]
      save_data()
      await send(message, "{mention} is no longer being ignored!".format(mention = member.mention))
    else:
      await send(message, "{name} is not currently ignored!".format(name = member.display_name))