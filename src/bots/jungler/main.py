import base64, discord, requests, traceback

from utils.datautils import config, data, default, save_data, set_client
from utils.discordbot import BotClient, send, get_member

from utils.lol.api import lol_region, watcher
from utils.lol.utils import lol_current_embed, lol_current_player_embed, lol_game_embed, lol_player_embed

client = None

class JunglerClient(BotClient):
  def __init__(self):
    BotClient.__init__(self)
    self.name = "jungler"

client = JunglerClient()

@client.command("Testing Commands", ["test"], "test", "Test the Jungler bot")
async def command_test(command, message):
  await send(message, "Test success!", reaction = "check")

@client.command("League Commands", ["lol", "report-player", "?", "?", "?"], "lol report-player [user = me] [index = last] [queue = all]", "generate a report for a player in a league of legends game")
@client.command("League Commands", ["lol", "report", "?", "?", "?"], "lol report [user = me + friend + ...] [index = last] [queue = all]", "generate a report for a league of legends game")
async def command_lol_report(command, message):
  if len(command) <= 2:
    if message.author.id not in (await default("lol_links", {})):
      await send(message, "You are not linked; use `pls lol link [user = me] <summoner>` to self-call the report command.", reaction = "x")
      summs = None
    else:
      summs = [(await data())["lol_links"][message.author.id]]
  else:
    summs = []
    for substr in command[2].split("+"):
      try:
        member = await get_member(message.guild, substr, message.author)
        summs.append((await data())["lol_links"][member.id])
      except:
        summs.append(substr)
  if summs:
    print("Beginning report...")
    fail = False
    index = (0 if command[3].lower() == "last" else int(command[3]) - 1) if len(command) > 3 else 0
    qids = {
      "all": {400, 420, 430, 440, 450, 700},
      "norms": {400, 430},
      "draft": {400},
      "blind": {430},
      "ranked": {420, 440},
      "solo": {420},
      "flex": {440},
      "aram": {450},
      "clash": {700}
    }
    print("Parsing queue types...")
    queuestring = command[4] if len(command) > 4 else "all"
    queuetypes = set()
    for queue in queuestring.split("|"):
      if queue.strip().lower() not in qids:
        await send(message, "Queue type not recognized! Allowed are: {qids}".format(qids = english_list(qids)), reaction = "x")
        break
      queuetypes |= qids[queue.strip().lower()]
    else:
      try:
        print("Fetching games (index %d, queues %s)..." % (index, queuetypes))
        games = watcher.match.matchlist_by_account(lol_region, watcher.summoner.by_name(lol_region, summs[0])["accountId"], queue = queuetypes, end_index = index + 1)["matches"]
      except Exception as e:
        print(traceback.format_exc())
        fail = True
      if not fail and len(games) > index:
        try:
          if command[1].lower() == "report":
            await send(message, embed = await lol_game_embed(message.guild, games[index]["gameId"], summs, False), reaction = "check")
          elif command[1].lower() == "report-player":
            await send(message, embed = await lol_player_embed(message.guild, games[index]["gameId"], summs[0], False), reaction = "check")
        except:
          print(traceback.format_exc())
          await send(message, "Failed to create embed!", reaction = "x")
      else:
        await send(message, "Could not find a game for {region}/{summoner} or summoner does not exist. Check your spelling; alternatively, this user has not played any games / enough games".format(
          region = lol_region.upper(),
          summoner = summs[0]
        ), reaction = "x")

@client.command("League Commands", ["lol", "current-player", "?"], "lol current-player [summoner = me + friend + ...]", "generate a detailed report for a player / players for the first player's current league of legends game")
@client.command("League Commands", ["lol", "current", "?"], "lol current [summoner = me + friend + ...]", "generate a report for a player's current league of legends game")
async def command_lol_current(command, message):
  if len(command) <= 2:
    if message.author.id not in (await default("lol_links", {})):
      await send(message, "You are not linked; use `pls lol link [user = me] <summoner>` to self-call the report command.", reaction = "x")
      summs = None
    else:
      summs = [(await data())["lol_links"][message.author.id]]
  else:
    summs = []
    for substr in command[2].split("+"):
      try:
        member = await get_member(message.guild, substr, message.author)
        summs.append((await data())["lol_links"][member.id])
      except:
        summs.append(substr)
  try:
    game = watcher.spectator.by_summoner(lol_region, watcher.summoner.by_name(lol_region, summs[0])["id"])
    try:
      if command[1] == "current":
        await send(message, embed = await lol_current_embed(message.guild, game, summs), reaction = "check")
      elif command[1] == "current-player":
        await send(message, embed = await lol_current_player_embed(message.guild, game, summs), reaction = "check")
    except:
      print(traceback.format_exc())
      await send(message, "Failed to create embed!", reaction = "x")
  except Exception as e:
    print(traceback.format_exc())
    await send(message, "Could not find current game for {region}/{summoner} or summoner does not exist! Check your spelling, or the summoner may not be in game.".format(
      region = lol_region.upper(),
      summoner = summs[0]
    ), reaction = "x")

@client.command("League Commands", ["lol", "link", ".+", "?"], "lol link <user> <summoner> | lol link (user = me) <summoner>", "link a user to a league of legends summoner")
async def command_lol_link(command, message):
  member = await get_member(message.guild, command[2], message.author) if len(command) > 3 else message.author
  summoner = command[3] if len(command) > 3 else command[2]
  old = (await default("lol_links", {})).get(member.id)
  (await data())["lol_links"][member.id] = summoner
  await save_data()
  await send(message, "Linked {name} to {region}/{summoner}{prev}!".format(
    name = member.display_name,
    region = lol_region.upper(),
    summoner = summoner,
    prev = " (previously {region}/{summoner})".format(region = lol_region.upper(), summoner = old) if old else ""
  ), reaction = "check")

@client.command("League Commands", ["lol", "unlink", "?"], "lol unlink [user = me]", "unlink a user from their league of legends summoner")
async def command_lol_unlink(command, message):
  member = await get_member(message.guild, command[2], message.author) if len(command) > 2 else message.author
  old = (await default("lol_links", {})).get(member.id)
  if old:
    del (await data())["lol_links"][member.id]
    await save_data()
    await send(message, "Unlinked {name} from {region}/{summoner}!".format(
      name = member.display_name,
      region = lol_region.upper(),
      summoner = old
    ), reaction = "check")
  else:
    await send(message, "{name} is not linked!".format(name = member.display_name), reaction = "x")

set_client(client)

def start():
  client.run(config["discord-tokens"]["jungler"])