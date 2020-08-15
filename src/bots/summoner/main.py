import asyncio

from .bot import client
from .botmanager import start, stop
from .callbackserver import start_server

from utils.datautils import config
  
async def heartbeat():
  while True:
    # print("Beep")
    await asyncio.sleep(1)

async def discord():
  await client.start(config["discord-tokens"]["summoner"])

def start():
  loop = asyncio.get_event_loop()
  loop.run_until_complete(asyncio.gather(
    heartbeat(),
    discord(),
    start_server()
  ))