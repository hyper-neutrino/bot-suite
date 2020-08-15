import base64, discord, requests

from utils.datautils import config
from utils.discordbot import BotClient, send

data = None
client = None

def alert(string):
  try:
    requests.get("http://127.0.0.1:5995/?bot=botlane&value=" + base64.b64encode(bytes(string, "utf-8")).decode("utf-8"))
  except:
    pass

class BotlaneClient(BotClient):
  def __init__(self):
    BotClient.__init__(self)
    self.name = "botlane"

  async def on_ready(self):
    alert("READY")
  
  async def on_connect(self):
    alert("CONNECT")
  
  async def on_disconnect(self):
    alert("DISCONNECT")

client = BotlaneClient()

@client.command("Testing Commands", ["test"], "test", "Test the Botlane bot")
async def command_test(command, message):
  await send(message, "Test success!", reaction = "check")

def start():
  client.run(config["discord-tokens"]["botlane"])