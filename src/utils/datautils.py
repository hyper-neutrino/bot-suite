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

async def data():
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
    await save_data()
  if not data_cache.get("working"):
    with open("data-backup.pickle", "rb") as f:
      with open("data.pickle", "wb") as g:
        g.write(f.read())
        await client.announce("Data contents are broken; retrieving from backup!")
    return await data()
  return data_cache

with open("config.json", "r") as f:
  config = json.load(f)

async def default(key, val, obj = None):
  save = False
  if obj is None:
    obj = await data()
    save = True
  if key not in obj:
    obj[key] = val
  if save:
    await save_data()
  return obj[key]

def discard(obj, key):
  if key in obj:
    del obj[key]

async def save_data():
  if data_cache.get("working"):
    with lock:
      with open("data.pickle", "wb") as f:
        pickle.dump(data_cache, f)
  else:
    await client.announce("Data contents are broken; did not save!")

def save_config():
  with open("config.json", "w") as f:
    json.dump(config, f)