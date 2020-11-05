import asyncio, base64, discord, math, praw, random, re, requests, time

from utils.datautils import config, data, default, save_data, set_client
from utils.discordbot import BotClient, send

client = None
connection = None

words = []
wordmap = {}

reddit = praw.Reddit(client_id = config["reddit"]["client-id"], client_secret = config["reddit"]["client-secret"], user_agent = config["reddit"]["user-agent"])

anagram_lock = asyncio.Lock()

def display(actual, scrambled, hint):
  if hint == 0: return scrambled
  cl = list(scrambled)
  start = actual[:hint if hint * 2 <= len(actual) else -hint]
  end = actual[-hint:]
  for c in start + end:
    cl.remove(c)
  return f"**{start}**{''.join(cl)}**{end}**"

async def anagram_function(message, answer = None, stop = False, start = False):
  global wordmap
  async with anagram_lock:
    if stop:
      if message.channel.id in (await default("anagrams", {})):
        actual, _, _, _ = (await data())["anagrams"][message.channel.id]
        if len(wordmap[tuple(sorted(actual))]) == 1:
          await send(message, f"Anagram puzzle ended! The correct answer was: '{actual}'.", reaction = "check")
        else:
          answers = ", ".join(f"'{ans}'" for ans in wordmap[tuple(sorted(actual))])
          await send(message, f"Anagram puzzle ended! The correct answers were: {answers}", reaction = "check")
        del (await data())["anagrams"][message.channel.id]
        await save_data()
      else:
        await send(message, "There is no anagram puzzle in this channel!", reaction = "x")
    if answer:
      correct = False
      if message.channel.id in (await default("anagrams", {})):
        actual, _, hint, timestamp = (await data())["anagrams"][message.channel.id]
        if sorted(answer.lower()) == sorted(actual.lower()) and answer.lower() in words:
          points = max(len(answer) - hint * 2, 0)
          bonus = 0
          if time.time() - timestamp <= 5:
            bonus = int(math.floor(points * 0.5))
          pp = (await default("puzzlepoints", {}))
          key = (message.guild.id, message.author.id)
          if key not in (await data())["puzzlepoints"]:
            (await data())["puzzlepoints"][key] = {}
            await save_data()
          if "anagram" not in (await data())["puzzlepoints"][key]:
            (await data())["puzzlepoints"][key]["anagram"] = 0
            await save_data()
          (await data())["puzzlepoints"][key]["anagram"] += points + bonus
          await save_data()
          bd = f" **+{bonus}**" if bonus else ""
          alts = ", ".join(wordmap[tuple(sorted(answer))] - {answer})
          ad = f" (Alternative answers: {alts})" if len(wordmap[tuple(sorted(answer))]) > 1 else ""
          await send(message, f"Congratulations to {message.author.mention} for winning the anagram puzzle! (+{points}{bd}){ad}", reaction = "check")
          correct = True
          (await default("anagramninja", {}))[message.channel.id] = (actual, time.time())
          await save_data()
          del (await data())["anagrams"][message.channel.id]
          await save_data()
          start = True
      if not correct and message.channel.id in (await default("anagramninja", {})):
        actual, timestamp = (await data())["anagramninja"][message.channel.id]
        if time.time() - timestamp <= 1 and sorted(answer.lower()) == sorted(actual.lower()) and answer.lower() in words:
          await send(message, f"{message.author.mention} L", reaction = "x")
    if start:
      if message.channel.id not in (await default("anagrams", {})):
        answer = random.choice(words)
        cl = list(answer)
        random.shuffle(cl)
        scrambled = "".join(cl)
        (await data())["anagrams"][message.channel.id] = (answer, scrambled, 0, time.time())
        await save_data()
        await send(message, f"Anagram puzzle! Solve for: '{scrambled}' ({len(scrambled)}).")
      else:
        actual, scrambled, hint, _ = (await data())["anagrams"][message.channel.id]
        await send(message, f"An anagram puzzle is already running! Solve for: '{display(actual, scrambled, hint)}' ({len(actual)}).", reaction = "x")
    await save_data()

class ToplaneClient(BotClient):
  def __init__(self):
    BotClient.__init__(self)
    self.name = "toplane"
  
  async def on_ready(self):
    await BotClient.on_ready(self)
    global words, wordmap
    with open("words.txt", "r") as f:
      words = list(map(str.strip, f.read().strip().splitlines()))
      wordmap = {}
      for word in words:
        (await default(tuple(sorted(word)), set(), wordmap)).add(word)

  async def process(self, message):
    await anagram_function(message, answer = re.sub("[?!.,\"'()\\[\\]{}> `*_~]", "", message.content.strip()))

def save_words():
  with open("words.txt", "w") as f:
    f.write("\n".join(words))

client = ToplaneClient()

@client.command("Testing Commands", ["test"], "test", "Test the Toplane bot")
async def command_test(command, message):
  await send(message, "Test success!", reaction = "check")

@client.command("Puzzle Commands", ["anagram"], "anagram", "alias for `anagram start`")
@client.command("Puzzle Commands", ["anagram", "start"], "anagram start", "start an anagram puzzle")
async def command_anagram_start(command, message):
  await anagram_function(message, start = True)

@client.command("Puzzle Commands", ["anagram", "stop"], "anagram stop", "stop the anagram puzzle")
async def command_anagram_stop(command, message):
  await anagram_function(message, stop = True)

@client.command("Puzzle Commands", ["anagram", "restart"], "anagram restart", "restart the anagram puzzle (functionally stop + start but thread-safe)")
async def command_anagram_restart(command, message):
  await anagram_function(message, stop = True, start = True)

@client.command("Puzzle Commands", ["anagram", "hint"], "anagram hint", "reveal one letter from the start and end of the anagram answer (decreases point value by 2)")
async def command_anagram_stop(command, message):
  if message.channel.id not in (await default("anagrams", {})):
    await send(message, "There is no anagram puzzle in this channel!", reaction = "x")
  else:
    answer, scrambled, hint, timestamp = (await data())["anagrams"][message.channel.id]
    hint += 1
    if hint * 2 >= len(answer) - 1:
      await anagram_function(message, stop = True)
    else:
      await send(message, f"Hint: the current puzzle starts with '{answer[:hint]}' and ends with '{answer[-hint:]}' ('{display(answer, scrambled, hint)}' ({len(answer)})).", reaction = "check")
      (await data())["anagrams"][message.channel.id] = (answer, scrambled, hint, timestamp)
      await save_data()

@client.command("Puzzle Commands", ["anagram", "reorder"], "anagram reorder", "reorder the anagram puzzle")
async def command_anagram_reorder(command, message):
  if message.channel.id not in (await default("anagrams", {})):
    await send(message, "There is no anagram puzzle in this channel!", reaction = "x")
  else:
    answer, scrambled, hint, timestamp = (await data())["anagrams"][message.channel.id]
    cl = list(scrambled)
    random.shuffle(cl)
    scrambled = "".join(cl)
    await send(message, f"Reordered: solve for '{display(answer, scrambled, hint)}'.", reaction = "check")
    (await data())["anagrams"][message.channel.id] = (answer, scrambled, hint, timestamp)
    await save_data()

@client.command("Puzzle Commands", ["anagram", "add", ".+"], "anagram add <word>", "add a word to the dictionary (must be all lowercase letters, at least 5 letters long)")
async def command_anagram_add(command, message):
  if re.match("[a-z]{5}[a-z]*", command[2]) is None:
    await send(message, "Invalid word! Must be all lowercase letters, at least 5 letters long.", reaction = "x")
  elif command[2] in words:
    await send(message, "That word is already in the dictionary!", reaction = "x")
  else:
    words.append(command[2])
    words.sort()
    (await default(tuple(sorted(command[2])), set(), wordmap)).add(command[2])
    save_words()
    await send(message, f"Added '{command[2]}' to the dictionary!", reaction = "check")

@client.command("Puzzle Commands", ["anagram", "rm", ".+"], "anagram rm <word>", "alias for `anagram remove`")
@client.command("Puzzle Commands", ["anagram", "remove", ".+"], "anagram remove <word>", "remove a word from the dictionary")
async def command_anagram_remove(command, message):
  if command[2] not in words:
    await send(message, "That word is not in the dictionary!", reaction = "x")
  else:
    words.remove(command[2])
    wordmap[tuple(sorted(command[2]))].discard(command[2])
    save_words()
    await send(message, f"Removed '{command[2]}' from the dictionary!", reaction = "check")

@client.command("Puzzle Commands", ["anagram", "leaderboard"], "anagram leaderboard", "display the anagram puzzle score leaderboard")
async def command_anagram_leaderboard(command, message):
  scores = []
  for gid, mid in (await default("puzzlepoints", {})):
    if gid != message.guild.id: continue
    points = (await data())["puzzlepoints"][(gid, mid)].get("anagram", 0)
    if points:
      scores.append((points, message.guild.get_member(mid)))
  scores.sort(reverse = True)
  await send(message, embed = discord.Embed(
    title = "Anagram Leaderboard",
    description = "\n".join(f"{member} - {score}" for score, member in scores) or "The leaderboard is empty!"
  ), reaction = "check")

@client.command("Reddit Commands", ["ket"], "ket", "alias for `cat`")
@client.command("Reddit Commands", ["cat"], "cat", "fetch a random cat image from /r/cat")
@client.command("Reddit Commands", ["mem"], "mem", "alias for `meme`")
@client.command("Reddit Commands", ["meme"], "meme", "fetch a random meme from /r/memes")
async def command_anagram_cat(command, message):
  if command[0] == "ket" and random.random() < 0.01:
    await send(message, f"{message.author.mention} overdosed on ketamine and died.", reaction = "x")
  else:
    while True:
      item = reddit.subreddit("cat" if command[0] == "ket" or command[0] == "cat" else "memes").random()
      if any(item.url.endswith(suffix) for suffix in [".jpg", ".png", ".gif"]) and (message.channel.is_nsfw() or not item.over_18):
        break
    await send(message, item.url, reaction = "check")

@client.command("Reddit Commands", ["jonk"], "jonk", "alias for `jonk`")
@client.command("Reddit Commands", ["joke"], "joke", "fetch a random joke from /r/jokes")
async def command_anagram_cat(command, message):
  if random.random() < 0.01:
    await send(message, f"{message.author.mention} **Discord** would like access to your camera.", reaction = "check")
  else:
    while True:
      item = reddit.subreddit("jokes").random()
      if item.selftext and (message.channel.is_nsfw() or not item.over_18):
        break
    await send(message, f"**{item.title}**\n{item.selftext}", reaction = "check")

@client.command("Miscellaneous Commands", ["roll", "?"], "roll [config: xdy+xdy-xdy+...+n default 1d6]", "roll a die / dice (`<x>d<y>` to roll `x` `y`-sided dice)")
async def command_roll(command, message):
  if len(command) > 1:
    dice_config = command[1]
  else:
    dice_config = "1d6"
  match = re.match(r"^([+-]?\d+d\d+)(([+-]\d+d\d+)*)([+-]\d+)?$", dice_config)
  if match is not None:
    a, b, _, c = match.groups()
    dc = a + (b or "") + (c or "")
    if not dc.startswith("+"):
      dc = "+" + dc
    breaks = [i for i, c in enumerate(dc) if c == "+" or c == "-"]
    blocks = [dc[s:e] for s, e in zip(breaks, breaks[1:])] + [dc[breaks[-1]:]]
    pos = []
    neg = []
    mod = 0
    for block in blocks:
      if "d" in block:
        x, y = map(int, block[1:].split("d"))
        rolls = [random.randint(1, y) for _ in range(x)]
        if block[0] == "+":
          pos.extend(rolls)
        else:
          neg.extend(rolls)
      else:
        mod = int(block)
    if 1 < len(pos) + len(neg) < 10:
      breakdown = ""
      if pos:
        breakdown += f"[ {', '.join(map(str, pos))} ]"
      if neg:
        breakdown += f" - [ {', '.join(map(str, pos))} ]"
      if mod > 0:
        breakdown += f" + {mod}"
      elif mod < 0:
        breakdown += f" - {-mod}"
      await send(message, f"{message.author.mention} rolled **{sum(pos) - sum(neg) + mod}**! ({breakdown})")
    else:
      await send(message, f"{message.author.mention} rolled **{sum(pos) - sum(neg) + mod}**!")
  else:
    await send(message, "Invalid dice configuration! The config must start with xdy (optionally +/- xdy), have zero or more +/- xdy, and optionally end with +/- a modifier.", reaction = "x")

@client.command("Miscellaneous Commands", ["rickroll", ".+"], "rickroll <channel>", "connect to a voice channel and play 'Never Gonna Give You Up' by Rick Astley")
@client.command("Miscellaneous Commands", ["stickbug", ".+"], "stickbug <channel>", "connect to a voice channel and play the stickbug song")
@client.command("Miscellaneous Commands", ["thx", ".+"], "thx <channel>", "connect to a voice channel and play the loudest sound created by humans")
async def command_rickroll(command, message):
  global connection
  if connection:
    await connection.disconnect()
    connection = None
  for channel in await message.guild.fetch_channels():
    if type(channel) == discord.VoiceChannel and channel.name == command[1]:
      connection = await channel.connect(timeout = 3)
      connection.play(await discord.FFmpegOpusAudio.from_probe(f"{command[0]}.mp3"))
  await send(message, "Enjoy :)", reaction = "check")

@client.command("Miscellaneous Commands", ["gtfo"], "gtfo", "alias for `disconnect`")
@client.command("Miscellaneous Commands", ["dc"], "dc", "alias for `disconnect`")
@client.command("Miscellaneous Commands", ["disconnect"], "disconnect", "disconnect from voice")
async def command_disconnect(command, message):
  global connection
  if connection:
    await connection.disconnect()
    connection = None
    await send(message, "Disconnected!", reaction = "check")
  else:
    await send(message, "I am not connected to any voice channels!", reaction = "x")

set_client(client)