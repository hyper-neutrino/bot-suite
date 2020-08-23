import base64, discord, requests

from utils.datautils import config, data, default, save_data, set_client
from utils.discordbot import BotClient, send, get_member, get_role, get_color, english_list

client = None

class SupportClient(BotClient):
  def __init__(self):
    BotClient.__init__(self)
    self.name = "support"

client = SupportClient()

@client.command("Testing Commands", ["test"], "test", "Test the Support bot")
async def command_test(command, message):
  await send(message, "Test success!", reaction = "check")

set_client(client)

def start():
  client.run(config["discord-tokens"]["support"])