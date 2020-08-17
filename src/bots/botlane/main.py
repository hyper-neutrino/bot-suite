import base64, discord, requests

from utils.datautils import config, set_client
from utils.discordbot import BotClient, send

client = None

class BotlaneClient(BotClient):
  def __init__(self):
    BotClient.__init__(self)
    self.name = "botlane"

client = BotlaneClient()

@client.command("Testing Commands", ["test"], "test", "Test the Botlane bot")
async def command_test(command, message):
  await send(message, "Test success!", reaction = "check")

set_client(client)

def start():
  client.run(config["discord-tokens"]["botlane"])