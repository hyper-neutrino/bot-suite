import base64, discord, requests

from utils.datautils import config
from utils.discordbot import BotClient, send

client = None

class JunglerClient(BotClient):
  def __init__(self):
    BotClient.__init__(self)
    self.name = "jungler"

client = JunglerClient()

@client.command("Testing Commands", ["test"], "test", "Test the Jungler bot")
async def command_test(command, message):
  await send(message, "Test success!", reaction = "check")

def start():
  client.run(config["discord-tokens"]["jungler"])