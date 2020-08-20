import praw, random

from utils.datautils import config, set_client, default, data, save_data
from utils.discordbot import BotClient, send

client = None

reddit = praw.Reddit(client_id = config["reddit"]["client-id"], client_secret = config["reddit"]["client-secret"], user_agent = config["reddit"]["user-agent"])

class NeutrinoClient(BotClient):
  def __init__(self):
    BotClient.__init__(self)
    self.name = "neutrino"

client = NeutrinoClient()

@client.command("Reddit Commands", ["ket"], "ket", "alias for `cat`")
@client.command("Reddit Commands", ["cat"], "cat", "fetch a random cat image from /r/cat")
@client.command("Reddit Commands", ["mem"], "mem", "alias for `meme`")
@client.command("Reddit Commands", ["meme"], "meme", "fetch a random meme from /r/memes")
async def command_anagram_cat(command, message):
  if command[0] == "ket" and random.random() < 0.01:
    await send(message, "{mention} overdosed on ketamine and died.".format(mention = message.author.mention), reaction = "x")
  else:
    while True:
      item = reddit.subreddit("cat" if command[0] == "ket" or command[0] == "cat" else "memes").random()
      if message.channel.is_nsfw() or not item.over_18:
        break
    await send(message, item.url, reaction = "check")

@client.command("Reddit Commands", ["jonk"], "jonk", "alias for `jonk`")
@client.command("Reddit Commands", ["joke"], "joke", "fetch a random joke from /r/jokes")
async def command_anagram_cat(command, message):
  if random.random() < 0.01:
    await send(message, "{mention} **Discord** would like access to your camera.".format(mention = message.author.mention), reaction = "check")
  else:
    while True:
      item = reddit.subreddit("jokes").random()
      if message.channel.is_nsfw() or not item.over_18:
        break
    await send(message, "**{title}**\n{body}".format(
      title = item.title,
      body = item.selftext
    ), reaction = "check")

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
  deleted = await message.channel.purge(limit = None, before = (await message.channel.fetch_message(eid)) if eid != -1 else None, after = msg)
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
  (await default("collapse", {}))[rid] = messages
  await save_data()
  await send(message, "Collapsed {len} messages! See them at {url}.".format(len = len(messages), url = "https://discord.hyper-neutrino.xyz/collapse/" + rid), reaction = "check")

set_client(client)

def start():
  client.run(config["discord-tokens"]["neutrino"])