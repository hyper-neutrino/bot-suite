import base64, datetime, discord, requests, traceback

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

@client.command("Link Commands", [".+", "link", ".+", "?"], "<lol | cf | dmoj> link <user> <account> | <type> link (user = me) <account>", "link a user to an external ID/account")
async def command_ext_link(command, message):
  if command[0] in ["lol", "cf", "dmoj"]:
    member = await get_member(message.guild, command[2], message.author) if len(command) > 3 else message.author
    ext = command[3] if len(command) > 3 else command[2]
    old = (await default("{et}_links".format(et = command[0]), {})).get(member.id)
    (await data())["{et}_links".format(et = command[0])][member.id] = ext
    await save_data()
    await send(message, "Linked {name} to {ext}{prev}!".format(
      name = member.display_name,
      ext = ext,
      prev = " (previously {ext})".format(ext = old) if old else ""
    ), reaction = "check")
  else:
    await send(message, "Service does not exist! Currently supported: `lol` for League of Legends, `cf` for Codeforces, `dmoj` for DMOJ.", reaction = "x")

@client.command("Link Commands", [".+", "unlink", "?"], "<lol | cf | dmoj> unlink [user = me]", "unlink a user from their external ID/account")
async def command_ext_unlink(command, message):
  if command[0] in ["lol", "cf", "dmoj"]:
    member = await get_member(message.guild, command[2], message.author) if len(command) > 2 else message.author
    old = (await default("{et}_links".format(et = command[0]), {})).get(member.id)
    if old:
      del (await data())["{et}_links".format(et = command[0])][member.id]
      await save_data()
      await send(message, "Unlinked {name} from {ext}!".format(
        name = member.display_name,
        ext = old
      ), reaction = "check")
    else:
      await send(message, "{name} is not linked!".format(name = member.display_name), reaction = "x")
  else:
    await send(message, "Service does not exist! Currently supported: `lol` for League of Legends, `cf` for Codeforces, `dmoj` for DMOJ.", reaction = "x")

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
  if summs is not None:
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
      await send(message, "You are not linked; use `pls lol link [user = me] <summoner>` to self-call the current report command.", reaction = "x")
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
  if summs is not None:
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

@client.command("Codeforces Commands", ["cf", "details", "?"], "cf details [account = me]", "get all public details of a codeforces user")
@client.command("Codeforces Commands", ["cf", "rank", "?"], "cf rank [account = me]", "alias for `cf rating`")
@client.command("Codeforces Commands", ["cf", "rating", "?"], "cf rating [account = me]", "get the current and maximum rank/rating of a codeforces user")
async def command_cf_details(command, message):
  if len(command) <= 2:
    if message.author.id not in (await default("cf_links", {})):
      await send(message, "You are not linked; use `pls cf link [user = me] [handle]` to self-call the rating command.", reaction = "x")
      cf = None
    else:
      cf = (await data())["cf_links"][message.author.id]
  else:
    try:
      member = await get_member(message.guild, command[2], message.author)
      cf = (await data())["cf_links"][member.id]
    except:
      cf = command[2]
  if cf is not None:
    rv = requests.get("https://codeforces.com/api/user.info?handles=" + cf).json()
    if rv["status"] == "OK":
      cfdata = rv["result"][0]
      if command[1] == "rank" or command[1] == "rating":
        await send(message, "{user} is rank {rank} [{rating}] (max {maxrank} [{maxrating}])!".format(
          user = cf,
          rank = cfdata["rank"],
          rating = cfdata["rating"],
          maxrank = cfdata["maxRank"],
          maxrating = cfdata["maxRating"]
        ), reaction = "check")
      elif command[1] == "details":
        embed = discord.Embed(title = cf, color = 0x3333AA, url = "https://codeforces.com/profile/" + cf).set_image(url = "http:" + cfdata["avatar"])
        for key, name in [
          ("email", "Email Address"),
          ("firstName", "First Name"),
          ("lastName", "Last Name"),
          ("organization", "Organization"),
          ("contribution", "Contribution"),
          ("friendOfCount", "Friend Of #")
        ]:
          if cfdata.get(key):
            embed.add_field(name = name, value = str(cfdata[key]))
        if cfdata.get("country") or cfdata.get("city"):
          embed.add_field(name = "Location", value = "{city}{country}".format(
            city = "{c}, ".format(c = cfdata["city"]) if cfdata.get("city") else "",
            country = cfdata["country"]
          ))
        embed.add_field(name = "Current Rank", value = "{rank} [{rating}]".format(rank = cfdata["rank"], rating = cfdata["rating"]))
        embed.add_field(name = "Maximum Rank", value = "{rank} [{rating}]".format(rank = cfdata["maxRank"], rating = cfdata["maxRating"]))
        embed.add_field(name = "Registered Since", value = datetime.datetime.fromtimestamp(cfdata["registrationTimeSeconds"]).strftime("%B %d, %Y at %H:%M:%S"))
        embed.add_field(name = "Last Seen Online", value = datetime.datetime.fromtimestamp(cfdata["lastOnlineTimeSeconds"]).strftime("%B %d, %Y at %H:%M:%S"))
        await send(message, embed = embed, reaction = "check")
    else:
      await send(message, "'{cf}' is not a Codeforces user!".format(cf = cf), reaction = "x")

@client.command("DMOJ Commands", ["dmoj", "details", "?"], "dmoj details [account = me]", "get all public details of a DMOJ user")
@client.command("DMOJ Commands", ["dmoj", "rank", "?"], "dmoj rank [account = me]", "alias for `dmoj rating`")
@client.command("DMOJ Commands", ["dmoj", "rating", "?"], "dmoj rating [account = me]", "get the current and maximum rank/rating of a DMOJ user")
async def command_dmoj_details(command, message):
  if len(command) <= 2:
    if message.author.id not in (await default("dmoj_links", {})):
      await send(message, "You are not linked; use `pls dmoj link [user = me] [handle]` to self-call the rating command.", reaction = "x")
      dm = None
    else:
      dm = (await data())["dmoj_links"][message.author.id]
  else:
    try:
      member = await get_member(message.guild, command[2], message.author)
      dm = (await data())["dmoj_links"][member.id]
    except:
      dm = command[2]
  if dm is not None:
    rv = requests.get("https://dmoj.ca/api/v2/user/" + dm).json()
    if "error" in rv:
      await send(message, "Error fetching DMOJ user details; likely user does not exist.", reaction = "x")
    else:
      dmdata = rv["data"]["object"]
      rating = dmdata["rating"]
      if rating < 1000:
        rank = "Newbie"
      elif rating < 1200:
        rank = "Amateur"
      elif rating < 1500:
        rank = "Expert"
      elif rating < 1800:
        rank = "Candidate Master"
      elif rating < 2200:
        rank = "Master"
      elif rating < 3000:
        rank = "Grandmaster"
      else:
        rank = "Target"
      if dmdata["rank"] == "admin":
        rank += " (Admin)"
      if command[1] == "rank" or command[1] == "rating":
        await send(message, "{user} is rank {rank} [{rating}]!".format(
          user = dmdata["username"],
          rank = rank,
          rating = rating
        ), reaction = "check")

set_client(client)

def start():
  client.run(config["discord-tokens"]["jungler"])