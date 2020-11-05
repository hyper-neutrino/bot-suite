import base64, discord, random, requests

from utils.datautils import config, data, default, save_data, set_client
from utils.discordbot import BotClient, send, get_member, get_role, get_color, english_list

client = None

class SupportClient(BotClient):
  def __init__(self):
    BotClient.__init__(self)
    self.name = "support"
  
  async def on_raw_reaction_add(self, payload):
    if payload.message_id == 767970087021707265:
      if payload.emoji.name == "1️⃣":
        await payload.member.add_roles(get_role(payload.member.guild, "legger"))
      if payload.emoji.name == "2️⃣":
        await payload.member.add_roles(get_role(payload.member.guild, "crewmate"))
      if payload.emoji.name == "3️⃣":
        await payload.member.add_roles(get_role(payload.member.guild, "minecrafter"))
      if payload.emoji.name == "4️⃣":
        await payload.member.add_roles(get_role(payload.member.guild, "traveler"))
  
  async def on_raw_reaction_remove(self, payload):
    guild = self.get_guild(payload.guild_id)
    if payload.message_id == 767970087021707265:
      if payload.emoji.name == "1️⃣":
        await guild.get_member(payload.user_id).remove_roles(get_role(guild, "legger"))
      if payload.emoji.name == "2️⃣":
        await guild.get_member(payload.user_id).remove_roles(get_role(guild, "crewmate"))
      if payload.emoji.name == "3️⃣":
        await guild.get_member(payload.user_id).remove_roles(get_role(guild, "minecrafter"))
      if payload.emoji.name == "4️⃣":
        await guild.get_member(payload.user_id).remove_roles(get_role(guild, "traveler"))

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
  rd = english_list(f"'{role}'" for role in roles)
  await send(message, f"Added {rd} to {member.display_name}!", reaction = "check")
  
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
  rd = english_list(f"'{role}'" for role in roles)
  await send(message, f"Removed {rd} from {member.display_name}!", reaction = "check")

@client.command("Role Commands", ["role", "list", "?"], "role list [role]", "list this guild's roles, or users in a role")
async def command_role_list(command, message):
  if len(command) > 2:
    role = get_role(message.guild, command[2])
    await send(message, f"'{command[2]}' has the following users: {english_list(member.display_name for member in role.members)}", reaction = "check")
  else:
    rd = english_list(f"'{role}'" for role in message.guild.roles[1:])
    await send(message, f"This guild's roles are: {rd}", reaction = "check")

@client.command("Role Commands", ["role", "colour", ".+", "?"], "role colour <role> [colour = 0]", "alias for `role color`")
@client.command("Role Commands", ["role", "color", ".+", "?"], "role color <role> [color = 0]", "recolor a role to a specific color (if not specified, uncolored)")
async def command_role_color(command, message):
  await get_role(message.guild, command[2]).edit(color = get_color(command[3] if len(command) > 3 else "0"))
  await send(message, f"Recolored '{command[2]}'!", reaction = "check")

@client.command("Role Commands", ["role", "rename", ".+", ".+"], "role rename <role> <name>", "rename a role")
async def command_role_rename(command, message):
  await get_role(message.guild, command[2]).edit(name = command[3])
  await send(message, f"Renamed '{command[2]}' to '{command[3]}'!", reaction = "check")

@client.command("User Utility Commands", ["alias", ".+", "?"], "alias <name> [user = none]", "alias a string to a user")
async def command_alias(command, message):
  existing = (await default("aliases", {})).get((message.guild.id, command[1].lower()))
  if existing:
    prev = await message.guild.fetch_member(existing)
  else:
    prev = None
  
  if len(command) > 2:
    member = await get_member(message.guild, command[2], message.author)
    (await data())["aliases"][(message.guild.id, command[1].lower())] = member.id
    await save_data()
    pd = f" (previously {prev.display_name})" if prev else ""
    await send(message, f"Aliased '{command[1].lower()}' to {member.display_name}{pd}!", reaction = "check")
  elif existing:
    del (await data())["aliases"][(message.guild.id, command[1].lower())]
    await save_data()
    await send(message, f"Unaliased '{command[1].lower()}' from {prev.display_name}!", reaction = "check")
  else:
    await send(message, f"'{command[1].lower()}' is not aliased to any user!", reaction = "check")

@client.command("User Utility Commands", ["user", "list"], "user list", "list all members of the server")
async def command_alias(command, message):
  await send(message, ", ".join(str(member) for member in message.guild.members), reaction = "check")

@client.command("Management Commands", ["collapse", "\d+", "?", "?"], "collapse <start id> [end id]", "delete messages between two messages and output a link to them")
async def command_collapse(command, message):
  sid = int(command[1])
  eid = int(command[2]) if len(command) > 2 else -1
  messages = []
  try:
    msg = await message.channel.fetch_message(sid)
    messages.append((msg.author.name, msg.content))
    await msg.delete()
  except:
    pass
  try:
    deleted = await message.channel.purge(limit = None, before = (await message.channel.fetch_message(eid)) if eid != -1 else None, after = msg)
  except:
    deleted = []
  for msg in sorted(deleted, key = lambda m: m.created_at.timestamp()):
    messages.append((msg.author.name, msg.content))
  try:
    msg = await message.channel.fetch_message(eid)
    messages.append((msg.author.name, msg.content))
    await msg.delete()
  except:
    pass
  rid = ""
  for _ in range(20):
    rid += random.choice("abcdefghijklmnopqrstuvwxyz0123456789")
  if len(messages) == 0:
    await send(message, "Didn't collapse anything!", reaction = "check")
  else:
    (await default("collapse", {}))[rid] = messages
    await save_data()
    await send(message, f"Collapsed {len(messages)} message{'' if len(messages) == 1 else 's'}! See {'it' if len(messages) == 1 else 'them'} at https://discord.hyper-neutrino.xyz/collapse/{rid}.", reaction = "check")

set_client(client)