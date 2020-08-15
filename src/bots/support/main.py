import base64, discord, requests

from utils.datautils import config
from utils.discordbot import BotClient, send, get_member, get_role, get_color, english_list

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
  
@client.command("Role Commands", ["gib", ".+", "+"], "gib <user> <role> <role> ...", "alias for `role give`")
@client.command("Role Commands", ["role", "give", ".+", "+"], "role give <user> <role> <role> ...", "give a role / roles to a user")
async def command_role_give(command, message):
  if command[0] == "gib":
    user = command[1]
    roles = command[2:]
  else:
    user = command[2]
    roles = command[3:]
  member = await get_member(message.guild, user, message.author)
  await member.add_roles(*[get_role(message.guild, role) for role in roles])
  await send(message, "Added {roles} to {user}!".format(
    roles = english_list("'{role}'".format(role = role) for role in roles),
    user = member.display_name
  ), reaction = "check")
  
@client.command("Role Commands", ["gibnt", ".+", "+"], "gibnt <user> <role> <role> ...", "alias for `role remove`")
@client.command("Role Commands", ["role", "rm", ".+", "+"], "role rm <user> <role> <role> ...", "alias for `role remove`")
@client.command("Role Commands", ["role", "remove", ".+", "+"], "role remove <user> <role> <role> ...", "remove a role / roles from a user")
async def command_role_remove(command, message):
  if command[0] == "gibnt":
    user = command[1]
    roles = command[2:]
  else:
    user = command[2]
    roles = command[3:]
  member = await get_member(message.guild, user, message.author)
  await member.remove_roles(*[get_role(message.guild, role) for role in roles])
  await send(message, "Removed {roles} from {user}!".format(
    roles = english_list("'{role}'".format(role = role) for role in roles),
    user = member.display_name
  ), reaction = "check")

@client.command("Role Commands", ["role", "list"], "role list", "list this guild's roles")
async def command_role_list(command, message):
  await send(message, "This guild's roles are: {roles}".format(
    roles = english_list("'{role}'".format(role = role.name) for role in message.guild.roles[1:])
  ), reaction = "check")

@client.command("Role Commands", ["role", "colour", ".+", "?"], "role colour <role> [colour = 0]", "alias for `role color`")
@client.command("Role Commands", ["role", "color", ".+", "?"], "role color <role> [color = 0]", "recolor a role to a specific color (if not specified, uncolored)")
async def command_role_color(command, message):
  await get_role(message.guild, command[2]).edit(color = get_color(command[3] if len(command) > 3 else "0"))
  await send(message, "Recolored '{role}'!".format(role = command[2]), reaction = "check")

@client.command("Role Commands", ["role", "rename", ".+", ".+"], "role rename <role> <name>", "rename a role")
async def command_role_rename(command, message):
  await get_role(message.guild, command[2]).edit(name = command[3])
  await send(message, "Renamed '{role}' to '{name}'!".format(role = command[2], name = command[3]))

def start():
  client.run(config["discord-tokens"]["support"])