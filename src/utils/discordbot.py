import ast, discord, re, shlex, traceback

from .datautils import load_data, save_data
from .errors import BotError
from .logging import log

emoji_cache = {}

def emojis(guild):
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

async def send(message, *args, **kwargs):
  reply = await message.channel.send(*args, **{a: kwargs[a] for a in kwargs if a != "reaction"})
  if "reaction" in kwargs:
    if type(kwargs["reaction"]) == list:
      reaction_list = kwargs["reaction"]
    else:
      reaction_list = [kwargs["reaction"]]
    for reaction in reaction_list:
      try:
        await message.add_reaction(emojis(message.guild).get(reaction, emoji_shorthand.get(reaction)))
      except:
        log("Failed to add emoji {emoji}".format(emoji = reaction), "ERROR")
  
  data = load_data()
  data["triggers"][reply.id] = message.id
  data["command_messages"][message.id] = reply.id
  save_data(data)

class BotClient(discord.Client):
  def __init__(self):
    discord.Client.__init__(self)
    self.commands = {}
    self.sections = []
    self.name = ""
    self.color = 0x3333AA
  
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
    embed = discord.Embed(
      title = "Help - Commands",
      description = "Commands for this bot ({name}). Prefixing a command with `please` instead of `pls` will do the same thing but output any errors into the channel instead of ignoring them.".format(name = self.name),
      color = self.color
    )
    
    for section in self.sections:
      if section == "": continue
      commands = []
      for _, syntax, description, _, _ in self.commands[section]:
        commands.append("`pls {syntax}`: {desc}".format(syntax = syntax, desc = description))
      embed.add_field(name = section, value = "\n".join(commands), inline = False)
    
    await send(message, embed = embed, reaction = "check")

  async def on_message(self, message):
    shlex_object = shlex.shlex(message.content)
    shlex_object.quotes += "`"
    components = []
    part = shlex_object.get_token()
    while part:
      if part[0] == part[-1] == "`":
        part = part[1:-1]
      elif part[0] == part[-1] and part[0] in ["'", '"']:
        try:
          part = ast.literal_eval(part)
        except:
          pass
      components.append(part)
      part = shlex_object.get_token()
    if not components: return
    lowered = list(map(str.lower, components))
    if lowered == ["pls", "help", self.name] or lowered == ["please", "help", self.name]:
      await self.help(message)
    if lowered[0] == "pls" or lowered[0] == "please":
      show_error = components[0] == "please"
      components = components[1:]
      for section in self.sections:
        for regex, _, _, process, case_sensitive in self.commands[section]:
          if not regex: continue
          if regex[-1] == "+":
            if len(components) < len(regex):
              continue
            patterns = regex[:-1]
          elif regex[-1] == "*":
            patterns = regex[:-1]
          else:
            patterns = regex[:]
          opts = 0
          while patterns[-1] == "?":
            patterns.pop()
            opts += 1
          if len(components) < len(patterns) or len(components) > len(patterns) + opts:
            continue
          for component, pattern in zip(components, patterns):
            try:
              if re.match("^{pattern}$".format(pattern = pattern if case_sensitive else pattern.lower()), component if case_sensitive else component.lower()) is None:
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
                await send(message, traceback.format_exc(), reaction = "!")
            break
        else:
          continue
        break
    await self.process(message)