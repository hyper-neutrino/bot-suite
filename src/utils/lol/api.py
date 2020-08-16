import requests

from riotwatcher import LolWatcher, ApiError

from utils.datautils import config

watcher = LolWatcher(config["api-keys"]["riot"], timeout = 5)
lol_region = "na1"
lol_version = watcher.data_dragon.versions_for_region(lol_region)["n"]["champion"]

# CHAMPIONS

champs = {}

champ_list = watcher.data_dragon.champions(lol_version, False, "en_US")

for key in champ_list["data"]:
  row = champ_list["data"][key]
  champs[int(row["key"])] = row["name"]

# RUNES

runes = {}

for tree in watcher.data_dragon.runes_reforged(lol_version):
  runes[tree["id"]] = tree
  for slot in tree["slots"]:
    for rune in slot["runes"]:
      runes[rune["id"]] = rune

shard_name = {
  5001: "HP",
  5002: "ARMOR",
  5003: "MR",
  5005: "AS",
  5007: "CDR",
  5008: "AF"
}

# SPELLS

summoner_spells = {}

spell_list = watcher.data_dragon.summoner_spells(lol_version)["data"]

for spell in spell_list.values():
  summoner_spells[spell["key"]] = spell["name"]

# ITEMS

lolitems = watcher.data_dragon.items(lol_version)["data"]

# QUEUES

q = requests.get("http://static.developer.riotgames.com/docs/lol/queues.json").json()

queues = {}

for queue in q:
  queues[queue["queueId"]] = (queue["map"], queue["description"])