import base64, discord, requests

from utils.datautils import load_config
from utils.discordbot import BotClient, send

data = None
client = None

def alert(string):
  try:
    requests.get("http://127.0.0.1:5995/?bot=support&value=" + base64.b64encode(bytes(string, "utf-8")).decode("utf-8"))
  except:
    pass

class SupportClient(BotClient):
  def __init__(self):
    BotClient.__init__(self)
    self.name = "support"

  async def on_ready(self):
    alert("READY")
  
  async def on_connect(self):
    alert("CONNECT")
  
  async def on_disconnect(self):
    alert("DISCONNECT")

client = SupportClient()

@client.command("Testing Commands", ["test"], "test", "Test the Support bot")
async def command_test(command, message):
  await send(message, "Test success!", reaction = "check")

def start():
  client.run(load_config()["discord-tokens"]["support"])