import asyncio, discord, json, os, re, requests, shlex, time, traceback

from aioconsole import ainput

from .datautils import config, data, save_data, default
from .errors import BotError
from .logging import log

emoji_cache = {}

def emojis(guild):
  if not guild: return {}
  if guild.id in emoji_cache:
    return emoji_cache[guild.id]
  emoji_cache[guild.id] = {}
  for emoji in guild.emojis:
    emoji_cache[guild.id][emoji.name] = emoji
  return emoji_cache[guild.id]

emoji_shorthand = {
  "!": "❗",
  "x": "❌",
  "check": "✅"
}

def english_list(items):
  items = list(map(str, items))
  if len(items) == 0:
    return "(empty list)"
  elif len(items) == 1:
    return items[0]
  elif len(items) == 2:
    return " and ".join(items)
  else:
    return ", ".join(items[:-1]) + ", and " + items[-1]

async def send(message, *args, **kwargs):
  if "embed" in kwargs:
    kwargs["embed"].set_footer(text = "Requested by {name}".format(name = message.author.display_name))
  reply = await message.channel.send(*args, **{a: kwargs[a] for a in kwargs if a != "reaction"})
  if "reaction" in kwargs:
    if type(kwargs["reaction"]) == list:
      reaction_list = kwargs["reaction"]
    else:
      reaction_list = [kwargs["reaction"]]
    for reaction in reaction_list:
      try:
        await message.add_reaction(emojis(message.guild).get(reaction, emoji_shorthand.get(reaction, reaction)))
      except:
        log("Failed to add emoji {emoji}".format(emoji = reaction), "ERROR")
  return reply

async def get_member(guild, string, caller = None):
  match = None
  for member in guild.members:
    if member.display_name == string or member.name == string:
      if match is not None:
        raise BotError("Found multiple users with that nickname/username; please narrow your search with a discriminator or by tagging the user.")
      match = member
  if match is not None:
    return match
  if re.match(r"^[^#]+#\d{4}$", string):
    username, discriminator = string.split("#")
    for member in guild.members:
      if member.name == username and member.discriminator == discriminator:
        return member
  elif re.match(r"<@!\d+>", string):
    uid = string[3:-1]
    for member in guild.members:
      if str(member.id) == uid:
        return member
  elif string.lower() == "me" or string.lower() == "myself":
    return caller
  if (guild.id, string.lower()) in (await default("aliases", {})):
    return await guild.fetch_member((await data())["aliases"][(guild.id, string.lower())])
  raise BotError("Found no users with that identity; please check your spelling.")

def get_role(guild, string):
  match = None
  for role in guild.roles:
    if role.name == string:
      if match:
        raise BotError("Found multiple roles called '{string}'".format(string = string))
      match = role
  if match is not None:
    return match
  raise BotError("Found no roles called '{string}'.".format(string = string))

def get_color(string):
  if string == "":
    return discord.Color(0)
  elif string.startswith("0x"):
    try:
      return discord.Color(int(string[2:], 16))
    except:
      pass
  elif string.isdigit():
    try:
      return discord.Color(int(string))
    except:
      pass
  elif string in ["teal", "dark_teal", "green", "dark_green", "blue", "dark_blue", "purple", "dark_purple", "magenta", "dark_magenta", "gold", "dark_gold", "orange", "dark_orange", "red", "dark_red", "lighter_grey", "lighter_gray", "dark_grey", "dark_gray", "light_grey", "light_gray", "darker_grey", "darker_gray", "blurple", "greyple"]:
    return getattr(discord.Color, string)()
  raise BotError("Invalid color format; 0x<hexcode>, integer, or a Discord template color.")

class BotClient(discord.Client):
  def __init__(self, prefix = "pls"):
    discord.Client.__init__(self)
    self.commands = {}
    self.sections = []
    self.name = ""
    self.prefix = prefix
    self.color = 0x3333AA
    
    self.gid = 699314655973212242
    self.cid = 741144497588535378
  
  async def on_ready(self):
    await (self.announce("Hello o/ I am now ready!"))
  
  async def announce(self, *args, **kwargs):
    for gid, cid in (await default("statreports", set())):
      print("Announcing to {gid}#{cid}".format(gid = gid, cid = cid))
      try:
        await self.get_guild(gid).get_channel(cid).send(*args, **kwargs)
      except:
        print("ERROR announcing")
        print(traceback.format_exc())
  
  def command(self, section, regex, syntax, description, case_sensitive = False):
    if section not in self.sections:
      self.sections.append(section)
    
    if section not in self.commands:
      self.commands[section] = []
    
    def __inner(process):
      self.commands[section].append((regex, syntax, description, process, case_sensitive))
      return process
    
    return __inner
  
  async def process(self, message):
    pass
  
  async def help(self, message):
    if self.prefix == "pls":
      embed = discord.Embed(
        title = "Help - Commands",
        description = "Commands for this bot ({name}). Prefixing a command with `please` instead of `pls` will do the same thing but output any errors into the channel instead of ignoring them.".format(name = self.name),
        color = self.color
      )
    else:
      embed = discord.Embed(
        title = "Help - Commands",
        color = self.color
      )
    
    for section in self.sections:
      if section == "": continue
      commands = []
      for _, syntax, description, _, _ in self.commands[section]:
        commands.append("`{prefix} {syntax}`: {desc}".format(prefix = self.prefix, syntax = syntax, desc = description))
      embed.add_field(name = section, value = "\n".join(commands), inline = False)
    
    await send(message, embed = embed, reaction = "check")

  async def on_message(self, message):
    if message.content == "!!forcekill" or message.content == "!!forcekill {name}".format(name = self.name) and message.author.id in config["global-arguments"]["sudo"]:
      await send(message, "**<shutting down...>**", reaction = "!")
      os.kill(os.getpid(), 9)
    try:
      if message.guild:
        key = (message.guild.id, message.author.id)
        if key in (await default("ignore", {})) and ((await data())["ignore"][key] == -1 or (await data())["ignore"][key] > time.time()):
          return
      if message.mention_everyone:
        emojimap = emojis(message.guild)
        if "ping" in emojimap:
          await message.add_reaction(emojimap["ping"])
      await self.process(message)
      components = shlex.split(message.content)
      if not components: return
      lowered = list(map(str.lower, components))
      if lowered == [self.prefix, "help"] + ([self.name] if self.name and self.prefix == "pls" else []) or self.prefix == "pls" and lowered == ["please", "help"] + ([self.name] if self.name else []):
        await self.help(message)
      if lowered[0] == self.prefix or self.prefix == "pls" and lowered[0] == "please":
        show_error = components[0] == "please"
        components = components[1:]
        for section in self.sections:
          for regex, _, _, process, case_sensitive in self.commands[section]:
            if not regex: continue
            infinite = False
            if regex[-1] == "+":
              if len(components) < len(regex):
                continue
              patterns = regex[:-1]
              infinite = True
            elif regex[-1] == "*":
              patterns = regex[:-1]
              infinite = True
            else:
              patterns = regex[:]
            opts = 0
            while patterns[-1] == "?":
              patterns.pop()
              opts += 1
            if len(components) < len(patterns) or not infinite and len(components) > len(patterns) + opts:
              continue
            for component, pattern in zip(components, patterns):
              try:
                if type(pattern) == str:
                  if re.match("^{pattern}$".format(pattern = pattern if case_sensitive else pattern.lower()), component if case_sensitive else component.lower()) is None:
                    break
                else:
                  if not pattern(component):
                    break
              except:
                log("Failed to parse pattern '{pattern}'".format(pattern = pattern), "ERROR")
                break
            else:
              try:
                await process(components, message)
              except BotError as e:
                await send(message, e.msg, reaction = "x")
              except Exception as e:
                if show_error:
                  print(traceback.format_exc())
                  await send(message, traceback.format_exc(), reaction = "!")
              break
          else:
            continue
          break
    except:
      pass
  
  async def edit_pfp(self, url):
    try:
      with open("log.txt", "a") as f:
        f.write(self.name + " - changing profile\n")
      await self.user.edit(avatar = requests.get(url).content)
      with open("log.txt", "a") as f:
        f.write("success!")
    except:
      with open("log.txt", "a") as f:
        f.write(traceback.format_exc() + "\n")
  
  async def dircomm(self, command):
    if command.startswith("profilepic "):
      print("Setting profile picture...")
      await self.edit_pfp(command[11:])
    elif command.startswith("gg "):
      print("Setting guild...")
      g = command[3:].strip()
      if g.isdigit():
        g = int(g)
        if self.get_guild(g):
          self.gid = g
        else:
          print("Guild does not exist / I am not in this guild!")
      else:
        for guild in self.guilds:
          if guild.name == g:
            self.gid = guild.id
            break
        else:
          print("Guild does not exist / I am not in this guild!")
    elif command.startswith("gc "):
      print("Setting channel...")
      c = command[3:].strip()
      if c.isdigit():
        c = int(c)
        if self.get_guild(self.gid).get_channel(c):
          self.cid = c
        else:
          print("Channel does not exist / I am not in this channel!")
      else:
        for channel in self.get_guild(self.gid).channels:
          if channel.name == c:
            self.cid = channel.id
            break
        else:
          print("Channel does not exist / I am not in this channel!")
    elif command.startswith("send "):
      print("Sending message...")
      m = command[5:].strip()
      await self.get_guild(self.gid).get_channel(self.cid).send(m)
  
  async def broadcasts(self):
    while True:
      try:
        await self.dircomm(await ainput())
      except:
        print(traceback.format_exc())
  
  def main(self):
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(
      self.broadcasts(),
      self.start(config["discord-tokens"][self.name])
    ))