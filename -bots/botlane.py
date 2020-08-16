import asyncio, base64, datetime, discord, json, math, pickle, praw, random, re, requests, shlex, sys, time, threading, traceback

from discord.ext import tasks, commands
from riotwatcher import LolWatcher, ApiError

def local_alert(string):
  try:
    requests.get("http://127.0.0.1:5995/botlane?value=" + base64.b64encode(bytes(string, "utf-8")).decode("utf-8"))
  except:
    pass

require_permission = False

print("Loading config and data...")

with open("config.json", "r") as f:
  config = json.load(f)

with open("data.pickle", "rb") as f:
  try:
    data = pickle.load(f)
  except:
    data = {}

print("Loading anagram puzzle data...")

with open("words.txt", "r") as f:
  words = f.read().strip().splitlines()

anagram_puzzle = {}
anagram_puzzle_ts = {}
anagram_hint = {}

anagram_lock = asyncio.Lock()

last_anagram_answer = {}
last_anagram_ts = {}

async def anagram_function(channel, message = None, answer = None, start = False):
  async with anagram_lock:
    if answer:
      if channel.id in anagram_puzzle and sorted(answer) == sorted(anagram_puzzle[channel.id]) and answer in words:
        points = max(len(answer) - anagram_hint.get(channel.id, 0) * 2, 0)
        bonus = 0
        if time.time() - anagram_puzzle_ts.get(channel.id, 0) <= 5:
          bonus = int(math.floor(points * 0.5))
        if message.author.id not in data()["guilds"][message.guild.id]["puzzlepoints"]:
          data()["guilds"][message.guild.id]["puzzlepoints"][message.author.id] = {}
        if "anagram" not in data()["guilds"][message.guild.id]["puzzlepoints"][message.author.id]:
          data()["guilds"][message.guild.id]["puzzlepoints"][message.author.id]["anagram"] = 0
        data()["guilds"][message.guild.id]["puzzlepoints"][message.author.id]["anagram"] += points
        await reply(message, "Congratulations to " + message.author.mention + " for winning the anagram puzzle! (+%d%s)" % (points, " **+%d**" % bonus if bonus else ""))
        await message.add_reaction("✅")
        last_anagram_answer[channel.id] = anagram_puzzle[channel.id]
        last_anagram_ts[channel.id] = time.time()
        del anagram_puzzle[channel.id]
        start = True
      elif channel.id in last_anagram_answer and channel.id in last_anagram_ts and sorted(answer) == sorted(last_anagram_answer[channel.id]) and time.time() - last_anagram_ts[channel.id] <= 1 and answer in words:
        await reply(message, message.author.mention + " L")
        await message.add_reaction("❌")
    if start:
      old_ans = anagram_puzzle.get(channel.id)
      word = random.choice(words)
      cl = list(word)
      random.shuffle(cl)
      scramble = "".join(cl)
      anagram_puzzle[channel.id] = list(word)
      anagram_puzzle_ts[channel.id] = time.time()
      anagram_hint[channel.id] = 0
      msg = "Anagram puzzle! Solve the anagram for: '" + scramble + "'. (%d)" % len(word)
      if old_ans:
        old_ans = "".join(old_ans)
        msg += " (The previous answer was " + old_ans + ")"
        last_anagram_answer[channel.id] = old_ans
        last_anagram_ts[channel.id] = time.time()
      if message:
        await reply(message, msg)
        await message.add_reaction("✅")
      else:
        await channel.send(msg)

print("Initializing Reddit API...")

reddit = praw.Reddit(client_id = config["reddit_client_id"], client_secret = config["reddit_client_secret"], user_agent = config["reddit_user_agent"])

print("Initializing League of Legends API and data...")

watcher = LolWatcher(config["riot_api_key"], timeout = 5)

lol_region = "na1"

champs = {}

runes = {}

summoner_spells = {}

shard_name = {
  5001: "HP",
  5002: "ARMOR",
  5003: "MR",
  5005: "AS",
  5007: "CDR",
  5008: "AF"
}

lol_version = watcher.data_dragon.versions_for_region(lol_region)["n"]["champion"]

lolitems = watcher.data_dragon.items(lol_version)["data"]

champ_list = watcher.data_dragon.champions(lol_version, False, "en_US")

for key in champ_list["data"]:
  row = champ_list["data"][key]
  champs[int(row["key"])] = row["name"]

for tree in watcher.data_dragon.runes_reforged(lol_version):
  runes[tree["id"]] = tree
  for slot in tree["slots"]:
    for rune in slot["runes"]:
      runes[rune["id"]] = rune

spell_list = watcher.data_dragon.summoner_spells(lol_version)["data"]

for spell in spell_list.values():
  summoner_spells[spell["key"]] = spell["name"]

q = requests.get("http://static.developer.riotgames.com/docs/lol/queues.json").json()

queues = {}

for queue in q:
  queues[queue["queueId"]] = (queue["map"], queue["description"])

emojis = {}

class RSError(Exception):
  def __init__(self, msg):
    self.msg = msg

def save_data():
  with open("data.pickle", "wb") as f:
    pickle.dump(data, f)

def save_config():
  with open("config.json", "w") as f:
    json.dump(config, f)

def english_list(strings):
  strings = list(strings)
  if len(strings) == 0:
    return "<empty>"
  elif len(strings) == 1:
    return strings[0]
  elif len(strings) == 2:
    return " and ".join(strings)
  else:
    return ", ".join(strings[:-1]) + ", and " + strings[-1]

async def get_member(guild, string, caller = None, die = False):
  matches = []
  for member in guild.members:
    if member.display_name == string or member.name == string:
      matches.append(member)
  if len(matches) == 1:
    return matches[0]
  elif len(matches) > 1:
    if die:
      raise RSError("Found multiple users with that nickname/username; please narrow your search with a discriminator or tagging the user.")
    return "multi-match"
  else:
    if re.match(r"^[^#]+#\d{4}$", string):
      username, discriminator = string.split("#")
      for member in guild.members:
        if member.name == username and member.discriminator == discriminator:
          return member
    elif re.match(r"<@!\d+>", string):
      uid = string[3:-1]
      for member in guild.members:
        if str(member.id) == uid:
          return member
    elif string.lower() == "me" or string.lower() == "myself":
      return caller or "caller"
  if string.lower() in data()["guilds"][guild.id]["aliases"]:
    return await guild.fetch_member(data()["guilds"][guild.id]["aliases"][string.lower()])
  if die:
    raise RSError("Found no users with that identity; please check your spelling.")
  return "no-match"

def get_role(guild, string, die = False):
  matches = []
  for role in guild.roles:
    if role.name == string:
      matches.append(role)
  if len(matches) == 1:
    return matches[0]
  elif len(matches) > 1:
    if die:
      raise RSError("Found multiple roles called '" + string + "'.")
    return "multi-match"
  else:
    if die:
      raise RSError("Found no roles called '" + string + "'.")
    return "no-match"

def get_color(string, die = False):
  if string == "":
    return discord.Color(0)
  elif string.startswith("0x"):
    try:
      return discord.Color(int(string[2:], 16))
    except:
      pass
  elif string.isdigit():
    try:
      return discord.Color(int(string))
    except:
      pass
  elif string in ["teal", "dark_teal", "green", "dark_green", "blue", "dark_blue", "purple", "dark_purple", "magenta", "dark_magenta", "gold", "dark_gold", "orange", "dark_orange", "red", "dark_red", "lighter_grey", "lighter_gray", "dark_grey", "dark_gray", "light_grey", "light_gray", "darker_grey", "darker_gray", "blurple", "greyple"]:
    return getattr(discord.Color, string)()
  if die:
    raise RSError("Invalid color format; 0x<hexcode>, integer, or a Discord template color.")
  return "invalid"

def top_role_position(member):
  return member.guild.roles.index(member.top_role)

def find_position(role, lane):
  if role == "SOLO":
    if lane == "TOP":
      return 0
    return 2
  elif role == "DUO_CARRY":
    return 3
  elif role == "DUO_SUPPORT":
    return 4
  else:
    return 1

def get_or_self(d, v, f = None):
  return (f or (lambda x: x))(d.get(v, v))

async def reply(message, *args, **kwargs):
  result = await message.channel.send(*args, **kwargs)
  data()["triggers"][result.id] = message.id
  data()["command_messages"][message.id] = result.id
  save_data()
  return result

def lol_game_embed(gid, game, names = [], skip_remake = False):
  print("Generating league embed (game)...")
  names = list(map(str.lower, names))
  details = watcher.match.by_id(lol_region, game)
  print("Acquired game details")
  if skip_remake and details["gameDuration"] < 300:
    return "remake"
  pteams = [[None] * 5, [None] * 5]
  pfill = [[], []]
  id_to_name = {}
  print("Mapping identities...")
  for ident in details["participantIdentities"]:
    id_to_name[ident["participantId"]] = ident["player"]["summonerName"]
  for participant in details["participants"]:
    attrs = (
      champs[participant["championId"]],
      id_to_name[participant["participantId"]]
    ) + (
      "/".join(str(participant["stats"][x]) for x in ["kills", "deaths", "assists"]),
      str(participant["stats"]["totalMinionsKilled"] + participant["stats"]["neutralMinionsKilled"]),
      str(participant["stats"]["goldEarned"])
    )
    ii = participant["teamId"] == 200
    index = find_position(participant["timeline"]["role"], participant["timeline"]["lane"])
    if pteams[ii][index] is None:
      pteams[ii][index] = attrs
    else:
      pfill[ii].append(attrs)
#   cols = list(zip(*players))
#   modcols = []
#   for col in cols:
#     ml = max(map(len, col))
#     modcols.append([item.ljust(ml) for item in col])
#   players = list(zip(*modcols))
  print("Processing combined data...")
  for ii in range(2):
    for i in range(5):
      if pteams[ii][i] is None:
        pteams[ii][i] = pfill[ii].pop()
  players = pteams[0] + pteams[1]
  vicleft = (details["teams"][0]["teamId"] == 100) == (details["teams"][0]["win"] == "Win")
  dmin, dsec = divmod(details["gameDuration"], 60)
  timedisplay = str(dmin) + ":" + str(dsec).zfill(2)
  teams = details["teams"] if details["teams"][0]["teamId"] == 100 else details["teams"][::-1]
  indexes = {team["teamId"]: i for i, team in enumerate(teams)}
  plists = [[] for _ in range(len(teams))]
  for participant in details["participants"]:
    plists[indexes[participant["teamId"]]].append(participant)
  gold = [sum(participant["stats"]["goldEarned"] for participant in plist) for plist in plists]
  print("Constructing embed...")
  try:
    embed = discord.Embed(
      title = "Game Report (" + ("%s - %s" % queues.get(details["queueId"], ("Unknown Map", "Unknown Gamemode"))) + ")",
      color = 0x3333AA
    ).add_field(
      name = "Game Data",
      value = "Patch " + ".".join(details["gameVersion"].split(".")[:2]) + "\n"
        + datetime.datetime.fromtimestamp(details["gameCreation"] / 1000).strftime("%B %d, %Y at %H:%M") + "\n"
        + "Game Duration: " + timedisplay + "\n",
      inline = False
    ).add_field(
      name = "Team 1 - " + ("Victory" if vicleft else "Defeat"),
      value = "/".join(str(sum(participant["stats"][stat] for participant in plists[0])) for stat in ["kills", "deaths", "assists"]) + " - " + str(gold[0]) + " G" + "\n" + "%s " * 10 % sum([(teams[0][x], get_or_self(emojis.get(gid, {}), y)) for x, y in [("towerKills", "turret"), ("inhibitorKills", "inhibitor"), ("baronKills", "baron_nashor"), ("dragonKills", "drake"), ("riftHeraldKills", "rift_herald")]], ()) + "\n\n" + ("**Bans**\n" + "\n".join(champs.get(ban["championId"], "No Ban") for ban in teams[0]["bans"]) + "\n\n" if teams[0].get("bans") else "") + "**Players**\n" + "\n\n".join(("%s (" + ("**" if player[1].lower() in names else "") + "%s" + ("**" if player[1].lower() in names else "") + ")\n%s - %s CS - %s G") % tuple(player) for player in players[:5])
    ).add_field(
      name = "Team 2 - " + ("Defeat" if vicleft else "Victory"),
      value = "/".join(str(sum(participant["stats"][stat] for participant in plists[1])) for stat in ["kills", "deaths", "assists"]) + " - " + str(gold[1]) + " G" + "\n" + "%s " * 10 % sum([(teams[1][x], get_or_self(emojis.get(gid, {}), y)) for x, y in [("towerKills", "turret"), ("inhibitorKills", "inhibitor"), ("baronKills", "baron_nashor"), ("dragonKills", "drake"), ("riftHeraldKills", "rift_herald")]], ()) + "\n\n" + ("**Bans**\n" + "\n".join(champs.get(ban["championId"], "No Ban") for ban in teams[1]["bans"]) + "\n\n" if teams[1].get("bans") else "") + "**Players**\n" + "\n\n".join(("%s (" + ("**" if player[1].lower() in names else "") + "%s" + ("**" if player[1].lower() in names else "") + ")\n%s - %s CS - %s G") % tuple(player) for player in players[5:])
    )
    print("Done!")
    return embed
  except:
    print("Errored!")
    print(traceback.format_exc())
    return discord.Embed(
      title = "Error",
      color = 0xFF5555
    ).add_field(
      name = "Error while constructing embed: league embed (game)",
      value = "```%s```" % traceback.format_exc()[:1000]
    )

def lol_player_embed(gid, game, name, skip_remake = False):
  print("Generating league embed (player)...")
  details = watcher.match.by_id(lol_region, game)
  print("Acquired game details")
  if skip_remake and details["gameDuration"] < 300:
    return "remake"
  pid = None
  for ident in details["participantIdentities"]:
    if ident["player"]["summonerName"] == name:
      pid = ident["participantId"]
  if not pid:
    return discord.Embed(
      title = "The player was not found in this game. This should never happen, so probably contact the developers.",
      color = 0xFF5555
    )
  for participant in details["participants"]:
    if participant["participantId"] == pid:
      break
  for team in details["teams"]:
    if team["teamId"] == participant["teamId"]:
      break
  sumstat = lambda key: sum(p["stats"][key] for p in details["participants"] if p["teamId"] == team["teamId"])
  stats = participant["stats"]
  CS = stats["totalMinionsKilled"] + stats["neutralMinionsKilled"]
  return discord.Embed(
    title = "Game Report - Detailed Player Report (%s - %s)" % queues.get(details["queueId"], ("Unknown Map", "Unknown Gamemode")),
    color = 0x3333AA
  ).add_field(
    name = "Build Information",
    value = "__%s__ (lvl %s) - %s\n\n%s __%s__ | %s + %s + %s\n%s %s | %s + %s | %s/%s/%s\n\n%s\n\n%s + %s" % (
      champs.get(participant["championId"], "Unknokwn Champion"),
      stats["champLevel"],
      "Victory" if stats["win"] else "Defeat",
      emojis.get(gid, {}).get(runes[stats["perk0"]]["name"].lower().replace(" ", "_"), ""),
      *[runes[stats["perk%d" % i]]["name"] for i in range(4)],
      emojis.get(gid, {}).get(runes[stats["perkSubStyle"]]["name"].lower().replace(" ", "_"), ""),
      runes[stats["perkSubStyle"]]["name"],
      *[runes[stats["perk%d" % i]]["name"] for i in range(4, 6)],
      *[shard_name[stats["statPerk%d" % i]] for i in range(3)],
      ", ".join(x["name"] for x in [lolitems.get(str(stats["item%d" % i])) for i in range(7)] if x),
      get_or_self(emojis.get(gid, {}), summoner_spells[str(participant["spell1Id"])]),
      get_or_self(emojis.get(gid, {}), summoner_spells[str(participant["spell2Id"])])
    ),
    inline = False
  ).add_field(
    name = "Performance",
    value = "%s/%s/%s - %s CS (%.1f / min) - %s G - %s%% KP\nVision: %s (Control Wards: %s; Wards Placed: %s; Wards Destroyed: %s)\nCC Score: %s\nKilling Sprees: %s (Largest: %s)\nMultikills: %s × Double, %s × Triple, %s × Quadra, %s × Penta\nLongest time alive: %s:%s" % (
      stats["kills"],
      stats["deaths"],
      stats["assists"],
      CS,
      CS / details["gameDuration"] * 60,
      stats["goldEarned"],
      int((stats["kills"] + stats["assists"]) * 100 / (sumstat("kills") or 1)),
      stats["visionScore"],
      stats["visionWardsBoughtInGame"],
      stats["wardsPlaced"],
      stats["wardsKilled"],
      stats["timeCCingOthers"],
      stats["killingSprees"],
      stats["largestKillingSpree"],
      stats["doubleKills"],
      stats["tripleKills"],
      stats["quadraKills"],
      stats["pentaKills"],
      stats["longestTimeSpentLiving"] // 60 if stats["longestTimeSpentLiving"] else "--",
      str(stats["longestTimeSpentLiving"] % 60).zfill(2) if stats["longestTimeSpentLiving"] else "--",
    ),
    inline = False
  ).add_field(
    name = "Damage/Healing Stats",
    value = "(Total, Magic, Physical, True)\nTotal Damage: %s (%s%%), %s (%s%%), %s (%s%%), %s (%s%%)\nChampion Damage: %s (%s%%), %s (%s%%), %s (%s%%), %s (%s%%)\nDamage Taken: %s (%s%%), %s (%s%%), %s (%s%%), %s (%s%%)\nDamage to turrets: %s (%s%%)\nDamage to objectives: %s (%s%%)\nSelf-mitigated damage: %s\nHealing done: %s (%s%%)" % (
      *sum([
        (lambda q: [
          stats[q],
          int(stats[q] * 100 / (sumstat(q) or 1))
        ])("magicalDamageTaken" if suff == "Taken" and key == "magicDamage" else key + suff) for suff in ("Dealt", "DealtToChampions", "Taken") for key in ("totalDamage", "magicDamage", "physicalDamage", "trueDamage")
      ], []),
      stats["damageDealtToTurrets"],
      int(stats["damageDealtToTurrets"] * 100 / (sumstat("damageDealtToTurrets") or 1)),
      stats["damageDealtToObjectives"],
      int(stats["damageDealtToObjectives"] * 100 / (sumstat("damageDealtToObjectives") or 1)),
      stats["damageSelfMitigated"],
      stats["totalHeal"],
      int(stats["totalHeal"] * 100 / (sumstat("totalHeal") or 1))
    ),
    inline = False
  ).add_field(
    name = "Timeline",
    value = "First Blood: %s\nFirst Tower: %s\nFirst Inhibitor: %s" % (
      *["✅" if stats.get("first%sKill" % val, False) else "Assisted" if stats.get("first%sAssist" % val, False) else "❌" for val in ["Blood", "Tower", "Inhibitor"]],
    )
  )

async def run_freerotation():
#   print("Checking Free Rotation...")
  try:
    rotation = requests.get("https://" + lol_region + ".api.riotgames.com/lol/platform/v3/champion-rotations?api_key=" + config["riot_api_key"]).json()["freeChampionIds"]
    if rotation != data()["lolrotation"]:
      data()["lolrotation"] = rotation
      print("(New Rotation: %s)" % english_list(champs[x] for x in rotation))
      save_data()
      for gid in data()["guilds"]:
        for cid in data()["guilds"][gid]["lolrotationwatch"]:
          channel = guilds_by_id[gid].get_channel(cid)
          await channel.send("New Free Rotation: " + english_list(champs[x] for x in rotation))
    else:
      pass
#       print("No new rotation.")
  except:
#     print("Free rotation watch failed; skipping this 10m block.")
    print(traceback.format_exc())
    return
  finally:
    pass
#     print("...Free Rotation Done!")

guilds_by_id = {}

connection = None

class FreeRotationCog(commands.Cog):
  def __init__(self):
    self.looper.start()
  
  def cog_unload(self):
    self.looper.cancel()
  
  @tasks.loop(seconds = 600)
  async def looper(self):
    await run_freerotation()

class RSClient(discord.Client):
  async def on_ready(self):
    global guilds_by_id
    print("Logged in as {0}!".format(self.user))
    await self.change_presence(activity = discord.Game(name = "pls help", type = 2))
    for guild in self.guilds:
      emojis[guild.id] = {}
      for emoji in guild.emojis:
        emojis[guild.id][emoji.name] = emojis[guild.id][emoji.id] = emoji
    save_data()
    print("Setup complete!")
    # LeagueWatcherCog()
    FreeRotationCog()
    local_alert("online")
  
  async def on_disconnect(self):
    local_alert("offline")
  
  async def on_guild_join(self, guild):
    global guilds_by_id
    guilds_by_id[guild.id] = guild
    if guild.id not in data()["guilds"]:
      data()["guilds"][guild.id] = {"members": {}, "aliases": {}, "leaguewatch": {}, "lolrotationwatch": set()}
    save_data()
  
  async def on_member_join(self, member):
    if member.id in data()["guilds"][member.guild.id]["members"] and "roles" in data()["guilds"][member.guild.id]["members"][member.id]:
      roles = [member.guild.get_role(rid) for rid in data()["guilds"][member.guild.id]["members"][member.id]["roles"]]
      await member.edit(roles = [role for role in roles if role])
      await member.create_dm()
      await member.dm_channel.send("Welcome back to " + member.guild.name + "! Your roles were restored.")
  
  async def on_member_remove(self, member):
    if member.id not in data()["guilds"][member.guild.id]["members"]:
      data()["guilds"][member.guild.id]["members"][member.id] = {}
    data()["guilds"][member.guild.id]["members"][member.id]["roles"] = [role.id for role in member.roles]
  
  async def on_message(self, message):
    global connection
    if message.mention_everyone and "ping" in emojis[message.guild.id]:
      await message.add_reaction(emojis[message.guild.id]["ping"])
    print("Received: " + repr(message.content))
    itime = data()["guilds"][message.guild.id]["members"].get(message.author.id, {}).get("ignore", 0)
    if message.author.id not in config["sudo"] and (itime == -1 or itime > time.time()):
      return
    try:
      command = shlex.split(message.content)
      if len(command) >= 2 and (command[0].lower() == "pls" or command[0].lower() == "please"):
        if command[1].lower() == "help" or command [1].lower() == "halp":
          await reply(message, embed = discord.Embed(
            title = "Riolku's Server Bot - Help",
            color = 0x3333AA
          ).add_field(
            name = "role commands",
            value = """`pls gib <user> <role...>` grant roles to a user
`pls give <user> <role...>` alias for `gib`
`pls gibnt <user> <role...>` remove roles from a user
`pls remove <user> <role...>` alias for `gibnt`
`pls list` list roles
`pls create <name> [color = none]` create a new role (no permissions, just for color); color as a word, 0x[hexcode], or integer RGB
`pls delet <role>` delete a role
`pls delete <role>` alias for `delet`
`pls color <role> [color = none]` edit the color of a role
`pls colour <role> [color = none]` alias for `color`
`pls hoist <role>` display a role separately in the user list
`pls unhoist <role>` don't display a role separately in the user list
`pls rename <role> <name>` rename a role
`pls bonk <user> [time = eternity]` make the bot ignore a user
`pls unbonk <user>` make the bot no longer ignore a user
""",
            inline = False
          ).add_field(
            name = "misc commands",
            value = """`pls help` display this message
`pls alias <a> [b]` alias the string <a> to mean user [b]; if [b] is not included, unalias <a>; aliases match after username, nickname, etc
`pls clean [limit = 100 ( / # / all)]` clean bot commands and outputs from the last [limit] messages
`pls ping` pong
`pls meme` fetch a meme from today's top posts in /r/memes
`pls roll [<x=1>d<y=6>+<v>...]` roll dice; default 1d6; `<x>d<y>` for `x` `y`-sided die; `<v>` to add `v`""",
            inline = False
          ).add_field(
            name = "puzzle commands",
            value = """`pls anagram` start an anagram puzzle; ends any running ones
`pls anagram hint` show one letter of the current word from the start and end
`pls anagram reorder` show a random reordering of the current anagram solution
`pls anagram leaderboard` show the leaderboard for the anagram puzzle
`pls anagram add <word>` add a word to the dictionary
`pls anagram remove <word> remove a word from the dictionary`
`pls <anagram of "anagram"> ...` alias for `pls anagram`""",
            inline = False
          ).add_field(
            name = "sensitive commands",
            value = """`pls auth` authorize a user to perform sensitive commands except auth/unauth
`pls unauth` unauthorize a user
`pls eval <...>` evaluate arbitrary Python code""",
            inline = False
          ).add_field(
            name = "reddit commands",
            value = """`pls meme` fetch a random meme from /r/memes
`pls mem` alias for `meme`
`pls cat` fetch a random cat pic from /r/cat
`pls ket` alias for `cat`""",
            inline = False
          ).add_field(
            name = "league of legends commands",
            value = """`pls lol report <summoner name> [index = last / #] [queue = all|... (all, norms (draft, blind), ranked (solo, flex), ARAM, clash)]` fetch the game report for this player's last game / nth last game
`pls lol report-game <summoner name> [index] [queue]` alias for `pls lol report`
`pls lol report-player <summoner name> [index] [queue]` fetch specific information about this player for a game
`pls lol current <summoner name>` fetch information about this summoner's current game
`pls lol watchrotation` watch free rotation in this channel
`pls lol unwatchrotation` unwatch free rotation in this channel
`pls lol link <account> <summoner name>` link a discord user to a summoner
`pls leg ...` alias for `pls lol`
`pls league ...` alias for `pls lol`""",
            inline = False
          ))
          await message.add_reaction("✅")
        if command[1].lower() == "gib" or command[1].lower() == "gibnt" or command[1].lower() == "give" or command[1].lower() == "remove":
          if require_permission and not message.author.guild_permissions.manage_roles:
            await reply(message, "You must have the `Manage Roles` permission to execute this command.")
            await message.add_reaction("❌")
          else:
            trp = top_role_position(message.author)
            member = await get_member(message.guild, command[2], message.author)
            roles = []
            multi_roles = []
            missing_roles = []
            forbidden_roles = []
            for string in command[3:]:
              role = get_role(message.guild, string)
              if role == "multi-match":
                multi_roles.append(string)
              elif role == "no-match":
                missing_roles.append(string)
              else:
                if False and message.guild.roles.index(role) >= trp: # TODO
                  forbidden_roles.append(role.name)
                roles.append(role)
            output = []
            if member == "multi-match":
              output.append("- Found multiple users with that nickname/username; please narrow your search with a discriminator or tagging the user.")
            elif member == "no-match":
              output.append("- Found no users with that identity; please check your spelling.")
            elif member == "caller":
              member = message.author
            if multi_roles:
              output.append("- Found multiple roles called " + english_list('"' + name + '"' for name in multi_roles) + ". Please rename your roles to be unique.")
            if missing_roles:
              output.append("- Found no roles called: " + english_list('"' + name + '"' for name in missing_roles) + ". Please check your spelling.")
            if forbidden_roles:
              output.append("- \"" + forbidden_roles[0] + "\" " + ("is" if len(forbidden_roles) == 1 else "are") + " equal to or higher than your highest role and thus you cannot grant/remove " + ("it" if len(forbidden_roles) == 1 else "them") + ".")
            if output:
              await reply(message, "\n".join(output))
              await message.add_reaction("❌")
            else:
              await (member.add_roles if command[1] == "gib" or command[1] == "give" else member.remove_roles)(*roles)
              if command[1] == "gib" or command[1] == "give":
                await reply(message, "Granted " + english_list('"' + role.name + '"' for role in roles) + " to " + member.display_name + ".")
                await message.add_reaction("✅")
              else:
                await reply(message, "Removed " + english_list('"' + role.name + '"' for role in roles) + " from " + member.display_name + ".")
                await message.add_reaction("✅")
        elif command[1].lower() == "list":
          if require_permission and not message.author.guild_permissions.manage_roles:
            await reply(message, "You must have the `Manage Roles` permission to execute this command.")
            await message.add_reaction("❌")
          else:
            output = ", ".join(["everyone"] + [role.name for role in message.guild.roles[1:]])
            if require_permission:
              await message.author.create_dm()
              await message.author.dm_channel.send(output)
              await reply(message, "Sent a DM with the role list for this server.")
              await message.add_reaction("✅")
            else:
              await reply(message, output)
              await message.add_reaction("✅")
        elif command[1].lower() == "meme" or command[1].lower() == "mem":
          while True:
            meme = reddit.subreddit("memes").random()
            if message.channel.is_nsfw() or not meme.over_18: break
          await reply(message, meme.url)
          await message.add_reaction("✅")
        elif command[1].lower() == "cat" or command[1].lower() == "ket":
          if command[1].lower() == "ket" and random.random() < 0.01:
            await reply(message, message.author.mention + " overdosed on ketamine and died.")
            await message.add_reaction("❌")
          else:
            while True:
              cat = reddit.subreddit("cat").random()
              if message.channel.is_nsfw() or not cat.over_18: break
            await reply(message, cat.url)
            await message.add_reaction("✅")
        elif command[1].lower() == "ping":
          await reply(message, "Pong! (%d ms)" % int((time.time() - (message.created_at - datetime.datetime(1970, 1, 1)) / datetime.timedelta(seconds = 1)) * 1000))
          await message.add_reaction("🏓")
        elif command[1].lower() == "auth" or command[1].lower() == "unauth":
          if not message.author.id in config["sudo"]:
            await reply(message, "You must be a sudo user to " + command[1] + "orize users.")
            await message.add_reaction("❌")
          else:
            member = await get_member(message.guild, command[2], message.author, True)
            if command[1].lower() == "auth" and member.id not in config["auth"]:
              config["auth"].append(member.id)
              save_config()
            elif command[1].lower() == "unauth" and member.id in config["auth"]:
              config["auth"].remove(member.id)
              save_config()
            await reply(message, member.display_name + " is now " + command[1] + "orized to perform sensitive commands.")
            await message.add_reaction("✅")
        elif command[1].lower() == "eval":
          if not message.author.id in config["sudo"] + config["auth"]:
            await reply(message, "You must be sudo/authorized to evaluate arbitrary code.")
            await message.add_reaction("❌")
          else:
            try:
              await reply(message, str(eval(message.content.split(maxsplit = 2)[2], dict(message = message, time = time, datetime = datetime), {})))
              await message.add_reaction("✅")
            except Exception as e:
              await reply(message, str(e))
              await message.add_reaction("❌")
        elif sorted(command[1].lower()) == list("aaagmnr"):
          if len(command) <= 2:
            await anagram_function(message.channel, message, start = True)
          elif command[2].lower() == "hint":
            if message.channel.id in anagram_puzzle:
              word = anagram_puzzle[message.channel.id]
              hint = anagram_hint.get(message.channel.id, 0) + 1
              anagram_hint[message.channel.id] = hint
              await reply(message, "Hint %d: The current word starts with '%s' and ends with '%s'" % (hint, "".join(word[:hint]), "".join(word[-hint:])))
              await message.add_reaction("✅")
            else:
              await reply(message, "There is no ongoing anagram puzzle in this channel.")
              await message.add_reaction("❌")
          elif command[2].lower() == "reorder":
            if message.channel.id in anagram_puzzle:
              word = anagram_puzzle[message.channel.id]
              charlist = list(word)
              random.shuffle(charlist)
              await reply(message, "Reordering of the anagram puzzle: '" + "".join(charlist) + "'.")
              await message.add_reaction("✅")
            else:
              await reply(message, "There is no ongoing anagram puzzle in this channel.")
              await message.add_reaction("❌")
          elif command[2].lower() == "leaderboard":
            leaderboard = []
            async for member in message.guild.fetch_members(limit = None):
              if member.id in data()["guilds"][message.guild.id]["puzzlepoints"] and "anagram" in data()["guilds"][message.guild.id]["puzzlepoints"][member.id]:
                leaderboard.append((data()["guilds"][message.guild.id]["puzzlepoints"][member.id]["anagram"], member))
            leaderboard.sort(reverse = True)
            await reply(message, embed = discord.Embed(
              title = "Anagram Leaderboard",
              color = 0x3333AA,
              description = "\n".join("%s: %s points" % (member.display_name, score) for score, member in leaderboard)
            ))
            await message.add_reaction("✅")
          elif command[2].lower() == "add":
            word = command[3].lower()
            if not word.isalpha():
              await reply(message, "Words must be alphabetical only.")
              await message.add_reaction("❌")
            elif word in words:
              await reply(message, "'" + word + "' is already in the dictionary.")
              await message.add_reaction("✅")
            else:
              words.append(word)
              words.sort()
              with open("words.txt", "w") as f:
                f.write("\n".join(words))
              await reply(message, "Added '" + word + "' to the dictionary.")
              await message.add_reaction("✅")
          elif command[2].lower() == "remove":
            word = command[3].lower()
            if word in words:
              words.remove(word)
              with open("words.txt", "w") as f:
                f.write("\n".join(words))
              await reply(message, "Removed '" + word + "' from the dictionary.")
              await message.add_reaction("✅")
            else:
              await reply(message, "'" + word + "' is not in the dictionary.")
              await message.add_reaction("✅")
        elif command[1].lower() == "roll":
          if len(command) <= 2:
            ans = random.randint(1, 6)
            await reply(message, str(ans))
            await message.add_reaction("✅")
          else:
            dl = command[2].split("+")
            failed = []
            ans = 0
            for die in dl:
              try:
                ans += int(die)
                continue
              except:
                pass
              comps = die.split("d")
              if len(comps) != 2:
                failed.append(die)
                continue
              L, R = comps
              if not (L.isdigit() or L == "") or not (R.isdigit() or R == ""):
                failed.append(die)
                continue
              n = int(L or "1")
              s = int(R or "6")
              if not failed:
                for _ in range(n):
                  ans += random.randint(1, s)
            if failed:
              await reply(message, "Dice format should be `<x>d<y>+...` for `x` `y`-sided dice; couldn't understand " + english_list("'" + die + "'" for die in failed) + ".")
              await message.add_reaction("❌")
            else:
              await reply(message, str(ans))
              await message.add_reaction("✅")
        elif command[1].lower() == "create":
          if require_permission and not message.author.guild_permissions.manage_roles:
            await reply(message, "You must have the `Manage Roles` permission to execute this command.")
            await message.add_reaction("❌")
          else:
            name = command[2]
            color = get_color(command[3].lower().replace(" ", "_")) if len(command) > 3 else discord.Color.default()
            output = []
            if color == "invalid":
              output.append("- Invalid color format; 0x<hexcode>, integer, or a Discord template color.")
            if any(role.name == name for role in message.guild.roles):
              output.append("- A role exists with this name already.")
            if output:
              await reply(message, "\n".join(output))
              await message.add_reaction("❌")
            else:
              try:
                await message.guild.create_role(name = name, color = color)
                await reply(message, "Created a new role.")
                await message.add_reaction("✅")
              except:
                await reply(message, "Unexpected error; perhaps the role name is invalid.")
                await message.add_reaction("❌")
        elif command[1].lower() == "delet" or command[1].lower() == "delete":
          if require_permission and not message.author.guild_permissions.manage_roles:
            await reply(message, "You must have the `Manage Roles` permission to execute this command.")
            await message.add_reaction("❌")
          else:
            await get_role(message.guild, command[2], True).delete()
            await reply(message, "Deleted role '" + command[2] + "'.")
            await message.add_reaction("✅")
        elif command[1].lower() == "color" or command[1].lower() == "colour":
          if require_permission and not message.author.guild_permissions.manage_roles:
            await reply(message, "You must have the `Manage Roles` permission to execute this command.")
            await message.add_reaction("❌")
          else:
            await get_role(message.guild, command[2], True).edit(color = get_color(command[3] if len(command) > 3 else "0", True))
            await reply(message, "Recolored '" + command[2] + "'.")
            await message.add_reaction("✅")
        elif command[1].lower() == "hoist" or command[1].lower() == "unhoist":
          if require_permission and not message.author.guild_permissions.manage_roles:
            await reply(message, "You must have the `Manage Roles` permission to execute this command.")
            await message.add_reaction("❌")
          else:
            await get_role(message.guild, command[2], True).edit(hoist = command[1] == "hoist")
            await reply(message, command[1][0].upper() + command[1][1:] + "ed '" + command[2] + "'.")
            await message.add_reaction("✅")
        elif command[1].lower() == "rename":
          if require_permission and not message.author.guild_permissions.manage_roles:
            await reply(message, "You must have the `Manage Roles` permission to execute this command.")
            await message.add_reaction("❌")
          else:
            await get_role(message.guild, command[2], True).edit(name = command[3])
            await reply(message, "'" + command[2] + "' has been renamed to '" + command[3] + "'.")
            await message.add_reaction("✅")
        elif command[1].lower() == "bonk":
          if require_permission and not message.author.guild_permissions.manage_roles:
            await reply(message, "You must have the `Manage Roles` permission to execute this command.")
            await message.add_reaction("❌")
          else:
            member = await get_member(message.guild, command[2], message.author, True)
            if member == message.author:
              await reply(message, "You cannot bonk yourself (you would not be able to unbonk yourself).")
              await message.add_reaction("❌")
            else:
              if member.id not in data()["guilds"][message.guild.id]["members"]:
                data()["guilds"][message.guild.id]["members"][member.id] = {}
              data()["guilds"][message.guild.id]["members"][member.id]["ignore"] = int(time.time()) + int(command[3]) if len(command) > 3 else -1
              if len(command) > 3:
                await reply(message, "Bonk! " + member.mention + " is being ignored for " + command[3] + " seconds.")
              else:
                await reply(message, "Bonk! " + member.mention + " is being ignored indefinitely.")
              await message.add_reaction("✅")
        elif command[1].lower() == "unbonk":
          if require_permission and not message.author.guild_permissions.manage_roles:
            await reply(message, "You must have the `Manage Roles` permission to execute this command.")
            await message.add_reaction("❌")
          else:
            member = await get_member(message.guild, command[2], message.author, True)
            if member.id not in data()["guilds"][message.guild.id]["members"]:
              data()["guilds"][message.guild.id]["members"][member.id] = {}
            data()["guilds"][message.guild.id]["members"][member.id]["ignore"] = 0
            save_data()
            await reply(message, member.mention + " is no longer being ignored.")
            await message.add_reaction("✅")
        elif command[1].lower() == "lol" or command[1].lower() == "leg" or command[1].lower() == "league":
          if command[2].lower() == "report" or command[2].lower() == "report-game" or command[2].lower() == "report-teams" or command[2].lower() == "report-player": # change to elif
            if len(command) <= 3:
              if message.author.id not in data()["summoner_by_id"]:
                await reply(message, "You are not linked; use `pls lol link <user> <summoner>` to self-call the report command.")
                await message.add_reaction("❌")
                summs = None
              else:
                summs = [data()["summoner_by_id"][message.author.id]]
            else:
              summs = []
              for substr in command[3].split("+"):
                member = await get_member(message.guild, substr, message.author, False)
                if type(member) == str or member.id not in data()["summoner_by_id"]:
                  summs.append(substr)
                else:
                  summs.append(data()["summoner_by_id"][member.id])
            if summs:
              print("Beginning report...")
              fail = False
              index = (0 if command[4].lower() == "last" else int(command[4]) - 1) if len(command) > 4 else 0
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
              queuestring = command[5] if len(command) > 5 else "all"
              queuetypes = set()
              for queue in queuestring.split("|"):
                if queue.strip().lower() not in qids:
                  await reply(message, "Queue type not recognized! Allowed are: " + english_list(qids))
                  await message.add_reaction("❌")
                  break
                queuetypes |= qids[queue.strip().lower()]
              else:
                try:
                  print("Fetching games (index %d, queues %s)..." % (index, queuetypes))
                  games = watcher.match.matchlist_by_account(lol_region, watcher.summoner.by_name(lol_region, summs[0])["accountId"], queue = queuetypes, end_index = index + 1)["matches"]
                except:
                  fail = True
                if not fail and len(games) > index:
                  if command[2].lower() == "report" or command[2].lower() == "report-game":
                    await reply(message, embed = lol_game_embed(message.guild.id, games[index]["gameId"], summs, False))
                    await message.add_reaction("✅")
                  elif command[2].lower() == "report-player":
                    await reply(message, embed = lol_player_embed(message.guild.id, games[index]["gameId"], summs[0], False))
                    await message.add_reaction("✅")
                else:
                  await reply(message, "Could not find a game for '" + summs[0] + "' (region " + lol_region.upper() + "). Check your spelling; alternatively, this user has not played any games / enough games.")
                  await message.add_reaction("❌")
          elif command[2].lower() == "current":
            print("Beginning current report...")
            try:
              game = watcher.spectator.by_summoner(lol_region, watcher.summoner.by_name(lol_region, command[3].split("+")[0])["id"])
              await reply(message, embed = lol_current_embed(message.guild.id, game, command[3].split("+")))
            except:
              await reply(message, "Could not find current game for '" + command[3].split("+")[0] + "' (region " + lol_region.upper() + "). Check your spelling, or the summoner may not be in game.")
              await message.add_reaction("❌")
          elif command[2].lower() == "watchrotation":
            data()["guilds"][message.guild.id]["lolrotationwatch"].add(message.channel.id)
            save_data()
            await reply(message, "Now watching free rotation in this channel.")
            await message.add_reaction("✅")
          elif command[2].lower() == "unwatchrotation":
            data()["guilds"][message.guild.id]["lolrotationwatch"] -= {message.channel.id}
            save_data()
            await reply(message, "No longer watching free rotation in this channel.")
            await message.add_reaction("✅")
          elif command[2].lower() == "link":
            member = await get_member(message.guild, command[3], message.author, True)
            data()["summoner_by_id"][member.id] = command[4]
            data()["id_by_summoner"][command[4]] = member.id
            save_data()
            await reply(message, "Linked " + member.display_name + " to " + lol_region.upper() + "/" + command[4] + ".")
            await message.add_reaction("✅")
          elif command[2].lower() == "unlink":
            member = await get_member(message.guild, command[3], message.author, True)
            del data()["id_by_summoner"][data()["summoner_by_id"][member.id]]
            del data()["summoner_by_id"][member.id]
            save_data()
            await reply(message, "Unlinked " + member.display_name + ".")
            await message.add_reaction("✅")
        elif command[1].lower() == "clean":
          async with message.channel.typing():
            limit = (None if command[2].lower() == "all" else int(command[2])) if len(command) > 2 else 100
            deleted = await message.channel.purge(limit = limit, check = lambda m: m.id in data()["triggers"] or m.id in data()["command_messages"] or m.author == message.guild.me)
            for m in deleted:
              if m.id in data()["triggers"]:
                del data()["triggers"][m.id]
              if m.id in data()["command_messages"]:
                del data()["command_messages"][m.id]
            response = await reply(message, "Deleted " + str(len(deleted)) + " message" + ("" if len(deleted) == 1 else "s") + ".")
            await message.add_reaction("✅")
            await message.delete(delay = 3)
            await response.delete(delay = 3)
        elif command[1].lower() == "alias":
          string = command[2].lower()
          if len(command) > 3:
            old = data()["guilds"][message.guild.id]["aliases"].get(string, None)
            if old: old = await message.guild.fetch_member(old)
            member = await get_member(message.guild, command[3], message.author, True)
            data()["guilds"][message.guild.id]["aliases"][string] = member.id
            await reply(message, "Aliased '" + string + "' to " + member.display_name + "%s." % (" (Previously " + old.display_name + ")" if old else ""))
          else:
            if string in data()["guilds"][message.guild.id]["aliases"]:
              member = await message.guild.fetch_member(data()["guilds"][message.guild.id]["aliases"][string])
              del data()["guilds"][message.guild.id]["aliases"][string]
              await reply(message, "Unaliased '" + string + "' from " + member.display_name + ".")
            else:
              await reply(message, "('" + string + "' was not aliased; no changes made.)")
          save_data()
          await message.add_reaction("✅")
        elif command[1].lower() == "rickroll":
          for channel in await message.guild.fetch_channels():
            if type(channel) == discord.VoiceChannel and channel.name == command[2]:
              connection = await channel.connect(timeout = 3)
              connection.play(await discord.FFmpegOpusAudio.from_probe("rickroll.mp3"))
          await reply(message, "Enjoy :)")
          await message.add_reaction("✅")
        elif command[1].lower() == "dc" or command[1].lower() == "gtfo":
          if connection:
            await connection.disconnect()
            connection = None
            await reply(message, "Disconnected.")
            await message.add_reaction("✅")
          else:
            await reply(message, "I am not connected to any voice channels.")
            await message.add_reaction("❌")
        elif command[1].lower() == "shut" or command[1].lower() == "silence" or command[1].lower() == "mute":
          member = await get_member(message.guild, command[2], message.author, True)
          await member.edit(mute = True)
          await reply(message, member.display_name + " is now silenced.")
        elif command[1].lower() == "unshut" or command[1].lower() == "unsilence" or command[1].lower() == "unmute":
          member = await get_member(message.guild, command[2], message.author, True)
          await member.edit(mute = False)
          await reply(message, member.display_name + " is no longer silenced.")
        elif command[1].lower() == "deafen":
          member = await get_member(message.guild, command[2], message.author, True)
          await member.edit(deafen = True)
          await reply(message, member.display_name + " is now deafened.")
        elif command[1].lower() == "undeafen":
          member = await get_member(message.guild, command[2], message.author, True)
          await member.edit(deafen = False)
          await reply(message, member.display_name + " is no longer deafened.")
    except RSError as e:
      await reply(message, e.msg)
      await message.add_reaction("❌")
    except ApiError as e:
      print(traceback.print_exc())
      await reply(message, "Riot API Error. Please try again. This is likely Riot's fault and we can't do anything about it.")
      await message.add_reaction("❌")
    except Exception as e:
      if message.content.startswith("please"):
        await reply(message, traceback.format_exc())
    if message.author != message.guild.me:
      trimmed_content = re.sub("[?!.,\"'()\\[\\]{}> `*_~]", "", message.content).lower()
      await anagram_function(message.channel, message, answer = trimmed_content)

print("Initializing client...")

client = RSClient()
client.run(config["token"])