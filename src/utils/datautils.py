import json, pickle, sys

from .logging import log

data = None
config = None

with open("data.pickle", "rb") as f:
  try:
    data = pickle.load(f)
  except:
    log("Failed to parse data file!", "ERROR")
    data = {}

with open("config.json", "r") as f:
  config = json.load(f)

def default(key, val, obj = None):
  if obj == None: obj = data
  if key not in obj:
    obj[key] = val
  return obj[key]

def save_data():
  with open("data.pickle", "wb") as f:
    pickle.dump(data, f)

def save_config():
  with open("config.json", "w") as f:
    json.dump(config, f)