import base64, discord, requests

from utils.datautils import config, set_client
from utils.discordbot import BotClient, send, english_list

from utils.lol.api import watcher, lol_region, lol_version, champs

client = None

class MidlaneClient(BotClient):
  def __init__(self):
    BotClient.__init__(self)
    self.name = "midlane"

client = MidlaneClient()

champions = watcher.data_dragon.champions(lol_version)["data"]

cmap = {}

for key in champions:
  cmap[champions[key]["id"].lower()] = cmap[champions[key]["name"].lower()] = champions[key]["id"]

@client.command("Testing Commands", ["test"], "test", "Test the Midlane bot")
async def command_test(command, message):
  await send(message, "Test success!", reaction = "check")

@client.command("League Research Commands", ["lol", "rotation"], "lol rotation", "check the current free champion rotation")
async def command_lol_rotation(command, message):
  champions = [champs[cid] for cid in watcher.champion.rotations(lol_region)["freeChampionIds"]]
  champions.sort()
  await send(message, f"This week's free rotation is: {english_list(champions)}.", reaction = "check")

@client.command("League Research Commands", ["lol", "ranges", "+"], "lol ranges <champion> [champion...]", "compare ability ranges for all champions")
async def command_lol_ranges(command, message):
  champs = set()
  for champ in command[2:]:
    champ = champ.lower()
    if champ not in cmap:
      await send(message, f"{champ} is not a recognized champion name or ID!", reaction = "x")
      break
    champs.add(cmap[champ])
  else:
    items = []
    for champ in champs:
      data = requests.get(f"http://ddragon.leagueoflegends.com/cdn/10.16.1/data/en_US/champion/{champ}.json").json()
      items.append((data["data"][champ]["stats"]["attackrange"], data["data"][champ]["name"], "Basic Attack"))
      for i, spell in enumerate(data["data"][champ]["spells"]):
        ident = data["data"][champ]["name"] + " " + ("QWER"[i] if 0 <= i < 4 else "?")
        if len(set(spell["range"])) == 1:
          items.append((spell["range"][0], ident, spell["name"]))
        else:
          clusters = {}
          for i, r in enumerate(spell["range"]):
            if r not in clusters:
              clusters[r] = []
            clusters[r].append(i + 1)
          for key in clusters:
            items.append((key, ident, spell["name"] + " Rank " + "/".join(map(str, clusters[key]))))
    items.sort()
    stacked = []
    for item in items:
      if stacked == [] or item[0] != stacked[-1][0]:
        stacked.append([item[0], []])
      stacked[-1][1].append((item[1], item[2]))
    info = "**Range Analysis**\n"
    for rng, stack in stacked:
      stack = ", ".join(f"{ident} ({name})" for ident, name in stack)
      info += f"\n__{rng}__: {stack}"
    await send(message, info, reaction = "check")

set_client(client)