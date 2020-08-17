import json, os, pickle, sys, traceback

from filelock import FileLock

from .logging import log

data_cache = None
config = None

last_time = -1

lock = FileLock("data.pickle.lock")

client = None

def set_client(cl):
  global client
  client = cl

def data():
  global data_cache, last_time
  mtime = os.stat("data.pickle").st_mtime
  if mtime > last_time or data_cache is None:
    mtime = last_time
    with lock:
      with open("data.pickle", "rb") as f:
        try:
          data_cache = pickle.load(f)
        except:
          log("Failed to parse data file!", "ERROR")
          print(traceback.format_exc())
          data_cache = {}
  if data_cache is None:
    data_cache = {}
    save_data()
  if not data_cache.get("working"):
    client.announce("Data file error! Reloading from the backup.")
    with open("data-backup.pickle", "rb") as f:
      with open("data.pickle", "wb") as g:
        g.write(f.read())
    return data()
  return data_cache

with open("config.json", "r") as f:
  config = json.load(f)

def default(key, val, obj = None):
  save = False
  if obj is None:
    obj = data()
    save = True
  if key not in obj:
    obj[key] = val
  if save:
    save_data()
  return obj[key]

def save_data():
  with lock:
    with open("data.pickle", "wb") as f:
      pickle.dump(data_cache, f)
    if data_cache.get("working"):
      with open("data.pickle", "rb") as f:
        with open("data-backup.pickle", "wb") as g:
          g.write(f.read())

def save_config():
  with open("config.json", "w") as f:
    json.dump(config, f)