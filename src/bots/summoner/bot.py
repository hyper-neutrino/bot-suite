import datetime, discord, time

from .botmanager import start, stop, aliases, titles, bots

from utils.datautils import config, data, save_data, default, set_client
from utils.discordbot import BotClient, send, get_member

client = None

botlist = ["toplane", "jungler", "midlane", "botlane", "support", "timer", "neutrino"]

class SummonerClient(BotClient):
  def __init__(self):
    BotClient.__init__(self)
    self.name = "summoner"

  async def process(self, message):
    print(f"[{message.author.display_name} in {message.guild.name}#{message.channel.name}] {message.content}")
    if message.author.id != self.user.id and "❤️" in message.content:
      await send(message, "❤️")

  async def on_ready(self):
    await (self.announce("Summoner is now online! Starting the other bots now."))
    
    for bot in botlist:
      start(bot)
    
  async def on_guild_join(self, guild):
    add_guild(data, guild)
    save_data(data)

client = SummonerClient()

@client.command("", ["help"], "", "")
async def command_help(command, message):
  await send(message, embed = discord.Embed(
    title = "BotSuite help",
    description = f"""`pls help < {" | ".join(botlist)} | summoner >`: help about a specific bot"""
  ), reaction = "check")

@client.command("Utility Commands", ["test"], "test", "Test the Summoner bot")
async def command_test(command, message):
  await send(message, "Test success!", reaction = "check")

@client.command("Utility Commands", ["ping"], "ping", "check your ping")
async def command_ping(command, message):
  ping = int((time.time() - (message.created_at - datetime.datetime(1970, 1, 1)) / datetime.timedelta(seconds = 1)) * 1000)
  await send(message, "Pong! ({ping} ms)", reaction = "🏓")

@client.command("Bot Manager Commands", ["statwatch"], "statwatch", "watch bot status reports in this channel")
async def command_statwatch(command, message):
  (await default("statreports", set())).add((message.guild.id, message.channel.id))
  await save_data()
  await send(message, "Now watching bot status reports in this channel!", reaction = "check")

@client.command("Bot Manager Commands", ["statunwatch"], "statunwatch", "stop watching bot status reports in this channel")
async def command_statunwatch(command, message):
  (await default("statreports", set())).discard((message.guild.id, message.channel.id))
  await save_data()
  await send(message, "No longer watching bot status reports in this channel!", reaction = "check")

@client.command("Bot Manager Commands", ["stop", ".+"], "stop <botname | all>", "stop a certain bot or all bots")
async def command_stop(command, message):
  if command[1] == "all":
    for bot in botlist:
      try:
        stop(bot)
      except:
        pass
    await send(message, "All bots have been killed!", reaction = "check")
  else:
    stop(command[1])
    await send(message, f"{titles[aliases[command[1]]]} has been killed!", reaction = "check")

@client.command("Bot Manager Commands", ["start", ".+"], "start <botname | all>", "start a certain bot or all bots")
async def command_stop(command, message):
  if command[1] == "all":
    for bot in botlist:
      try:
        start(bot)
      except:
        pass
    await send(message, "All bots are being started!", reaction = "check")
  else:
    start(command[1])
    await send(message, f"{titles[aliases[command[1]]]} is being started!", reaction = "check")

@client.command("Bot Manager Commands", ["restart", ".+"], "restart <botname | all>", "restart a certain bot or all bots (functionally `stop` + `start`)")
async def command_restart(command, message):
  if command[1] == "all":
    for bot in botlist:
      try:
        stop(bot)
        start(bot)
      except:
        pass
    await send(message, "All bots are being restarted!", reaction = "check")
  else:
    stop(command[1])
    start(command[1])
    await send(message, f"{titles[aliases[command[1]]]} is being restarted!", reaction = "check")

@client.command("Bot Manager Commands", ["bonk", ".+", "?"], "bonk <user> [time]", "alias for `ignore`")
@client.command("Bot Manager Commands", ["ignore", ".+", "?"], "ignore <user> [time]", "ignore a user until [time] seconds from now")
async def command_ignore(command, message):
  if len(command) > 2 and not command[2].isdigit():
    await send(message, "Invalid time! Must be an integer.", reaction = "x")
  else:
    member = await get_member(message.guild, command[1], message.author)
    if member == message.author:
      await send(message, f"You cannot {command[0]} yourself!")
    elif member.id in config["global-arguments"]["sudo"]:
      await send(message, f"You cannot {command[0]} {member.display_name} as they are a sudo user!", reaction = "check")
    else:
      (await default("ignore", {}))[(message.guild.id, member.id)] = time.time() + int(command[2]) if len(command) > 2 else -1
      await save_data()
      if len(command) > 2:
        await send(message, f"{('Bonk! ' if command[0] == 'bonk' else '')}{member.mention} is being ignored for {command[2]} second{'' if command[2] == '1' else 's'}!")
      else:
        await send(message, f"{('Bonk! ' if command[0] == 'bonk' else '')}{member.mention} is being ignored indefinitely!", reaction = "check")

@client.command("Bot Manager Commands", ["unbonk", ".+", "?"], "unbonk <user>", "alias for `unignore`")
@client.command("Bot Manager Commands", ["unignore", ".+", "?"], "unignore <user>", "stop ignoring a user immediately (essentially `ignore <user> 0`)")
async def command_unignore(command, message):
  member = await get_member(message.guild, command[1], message.author)
  if member == message.author:
    await send(message, "If you were ignored, you would not be able to unignore yourself. Since you aren't, this command doesn't change anything. Please reconsider your choices.", reaction = "x")
  else:
    key = (message.guild.id, member.id)
    if key in (await default("ignore", {})) and ((await data())["ignore"][key] == -1 or (await data())["ignore"][key] > time.time()):
      del (await data())["ignore"][key]
      await save_data()
      await send(message, f"{member.mention} is no longer being ignored!", reaction = "check")
    else:
      await send(message, f"{member.display_name} is not currently ignored!", reaction = "x")

set_client(client)