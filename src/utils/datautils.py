import json, pickle, sys

from .logging import log

def load_data(filename = "data.pickle"):
  with open(filename, "rb") as f:
    try:
      return pickle.load(f)
    except:
      log("Failed to parse data file!", "ERROR")
      return {}

def setup_data(data, guilds):
  if "guilds" not in data: data["guilds"] = {}
  if "lolrotation" not in data: data["lolrotation"] = 0
  if "triggers" not in data: data["triggers"] = {}
  if "command_messages" not in data: data["command_messages"] = {}
  if "summoner_by_id" not in data: data["summoner_by_id"] = {}
  if "id_by_summoner" not in data: data["id_by_summoner"] = {}
  for guild in guilds:
    add_guild(data, guild)

def add_guild(data, guild):
  if guild.id not in data["guilds"]:
    data["guilds"][guild.id] = {}

  for key in ("members", "aliases", "puzzlepoints"):
    if key not in data["guilds"][guild.id]:
      data["guilds"][guild.id][key] = {}

  for key in ("lolrotationwatch", "statreports"):
    if key not in data["guilds"][guild.id]:
      data["guilds"][guild.id][key] = set()

def save_data(data, filename = "data.pickle"):
  with open(filename, "wb") as f:
    pickle.dump(data, f)

def load_config(filename = "config.json"):
  with open(filename, "r") as f:
    return json.load(f)