import base64, discord, requests

from utils.datautils import config, set_client
from utils.discordbot import BotClient, send

client = None

class MidlaneClient(BotClient):
  def __init__(self):
    BotClient.__init__(self)
    self.name = "midlane"

client = MidlaneClient()

@client.command("Testing Commands", ["test"], "test", "Test the Midlane bot")
async def command_test(command, message):
  await send(message, "Test success!", reaction = "check")

set_client(client)

def start():
  client.run(config["discord-tokens"]["midlane"])