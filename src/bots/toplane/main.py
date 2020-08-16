import asyncio, base64, discord, math, praw, random, re, requests, time

from utils.datautils import config, data, default, save_data
from utils.discordbot import BotClient, send

client = None

reddit = praw.Reddit(client_id = config["reddit"]["client-id"], client_secret = config["reddit"]["client-secret"], user_agent = config["reddit"]["user-agent"])

anagram_lock = asyncio.Lock()

def display(actual, scrambled, hint):
  if hint == 0: return scrambled
  cl = list(scrambled)
  start = actual[:hint if hint * 2 <= len(actual) else -hint]
  end = actual[-hint:]
  for c in start + end:
    cl.remove(c)
  return "**{start}**{mid}**{end}**".format(
    start = start,
    mid = "".join(cl),
    end = end
  )

async def anagram_function(message, answer = None, stop = False, start = False):
  global wordmap
  async with anagram_lock:
    if stop:
      if message.channel.id in default("anagrams", {}):
        actual, _, _, _ = data()["anagrams"][message.channel.id]
        if len(wordmap[tuple(sorted(actual))]) == 1:
          await send(message, "Anagram puzzle ended! The correct answer was: '{actual}'.".format(actual = actual), reaction = "check")
        else:
          await send(message, "Anagram puzzle ended! The correct answers were: {answers}".format(
            answers = ", ".join("'{word}'".format(word = ans) for ans in wordmap[tuple(sorted(actual))])
          ))
        del data()["anagrams"][message.channel.id]
        save_data()
      else:
        await send(message, "There is no anagram puzzle in this channel!", reaction = "x")
    if answer:
      correct = False
      if message.channel.id in default("anagrams", {}):
        actual, _, hint, timestamp = data()["anagrams"][message.channel.id]
        if sorted(answer.lower()) == sorted(actual.lower()) and answer.lower() in words:
          points = max(len(answer) - hint * 2, 0)
          bonus = 0
          if time.time() - timestamp <= 5:
            bonus = int(math.floor(points * 0.5))
          default("anagram", 0, default((message.guild.id, message.author.id), {}, default("puzzlepoints", {})))
          data()["puzzlepoints"][(message.guild.id, message.author.id)]["anagram"] += points + bonus
          save_data()
          await send(message, "Congratulations to {name} for winning the anagram puzzle! (+{points}{bonus}){alternatives}".format(
            name = message.author.mention,
            points = points,
            bonus = " **+{val}**".format(val = bonus) if bonus else "",
            alternatives = " (Alternative answers: {answers})".format(
              answers = ", ".join("'{word}'".format(word = alt) for alt in wordmap[tuple(sorted(answer))] - {answer})
            ) if len(wordmap[tuple(sorted(answer))]) > 1 else ""
          ), reaction = "check")
          correct = True
          default("anagramninja", {})[message.channel.id] = (actual, time.time())
          del data()["anagrams"][message.channel.id]
          save_data()
          start = True
      if not correct and message.channel.id in default("anagramninja", {}):
        actual, timestamp = data()["anagramninja"][message.channel.id]
        if time.time() - timestamp <= 1 and sorted(answer.lower()) == sorted(actual.lower()) and answer.lower() in words:
          await send(message, "{user} L".format(user = message.author.mention), reaction = "x")
    if start:
      if message.channel.id not in default("anagrams", {}):
        answer = random.choice(words)
        cl = list(answer)
        random.shuffle(cl)
        scrambled = "".join(cl)
        data()["anagrams"][message.channel.id] = (answer, scrambled, 0, time.time())
        save_data()
        await send(message, "Anagram puzzle! Solve for: '{scrambled}'.".format(scrambled = scrambled))
      else:
        actual, scrambled, hint, _ = data()["anagrams"][message.channel.id]
        await send(message, "An anagram puzzle is already running! Solve for: '{display}'.".format(
          display = display(actual, scrambled, hint)
        ), reaction = "x")
    save_data()

class ToplaneClient(BotClient):
  def __init__(self):
    BotClient.__init__(self)
    self.name = "toplane"

  async def process(self, message):
    await anagram_function(message, answer = re.sub("[?!.,\"'()\\[\\]{}> `*_~]", "", message.content.strip()))

with open("words.txt", "r") as f:
  words = list(map(str.strip, f.read().strip().splitlines()))
  wordmap = {}
  for word in words:
    default(tuple(sorted(word)), set(), wordmap).add(word)

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
async def command_anagram_stop(command, message):
  await anagram_function(message, stop = True, start = True)

@client.command("Puzzle Commands", ["anagram", "hint"], "anagram hint", "reveal one letter from the start and end of the anagram answer (decreases point value by 2)")
async def command_anagram_stop(command, message):
  if message.channel.id not in default("anagrams", {}):
    await send(message, "There is no anagram puzzle in this channel!", reaction = "x")
  else:
    answer, scrambled, hint, timestamp = data()["anagrams"][message.channel.id]
    hint += 1
    if hint * 2 >= len(answer):
      await anagram_function(message, stop = True)
    else:
      await send(message, "Hint: the current puzzle starts with '{start}' and ends with '{end}' ('{display}').".format(
        start = answer[:hint],
        end = answer[-hint:],
        display = display(answer, scrambled, hint)
      ), reaction = "check")
      data()["anagrams"][message.channel.id] = (answer, scrambled, hint, timestamp)
      save_data()

@client.command("Puzzle Commands", ["anagram", "reorder"], "anagram reorder", "reorder the anagram puzzle")
async def command_anagram_reorder(command, message):
  if message.channel.id not in default("anagrams", {}):
    await send(message, "There is no anagram puzzle in this channel!", reaction = "x")
  else:
    answer, scrambled, hint, timestamp = data()["anagrams"][message.channel.id]
    cl = list(scrambled)
    random.shuffle(cl)
    scrambled = "".join(cl)
    await send(message, "Reordered: solve for '{display}'.".format(display = display(answer, scrambled, hint)), reaction = "check")
    data()["anagrams"][message.channel.id] = (answer, scrambled, hint, timestamp)
    save_data()

@client.command("Puzzle Commands", ["anagram", "add", ".+"], "anagram add <word>", "add a word to the dictionary (must be all lowercase letters, at least 5 letters long)")
async def command_anagram_add(command, message):
  if re.match("[a-z]{5}[a-z]*", command[2]) is None:
    await send(message, "Invalid word! Must be all lowercase letters, at least 5 letters long.", reaction = "x")
  elif command[2] in words:
    await send(message, "That word is already in the dictionary!", reaction = "x")
  else:
    words.append(command[2])
    words.sort()
    default(tuple(sorted(command[2])), set(), wordmap).add(command[2])
    save_words()
    await send(message, "Added '{word}' to the dictionary!".format(word = command[2]), reaction = "check")

@client.command("Puzzle Commands", ["anagram", "rm", ".+"], "anagram rm <word>", "alias for `anagram remove`")
@client.command("Puzzle Commands", ["anagram", "remove", ".+"], "anagram remove <word>", "remove a word from the dictionary")
async def command_anagram_remove(command, message):
  if command[2] not in words:
    await send(message, "That word is not in the dictionary!", reaction = "x")
  else:
    words.remove(command[2])
    wordmap[tuple(sorted(command[2]))].discard(command[2])
    save_words()
    await send(message, "Removed '{word}' from the dictionary!".format(word = command[2]), reaction = "check")

@client.command("Puzzle Commands", ["anagram", "leaderboard"], "anagram leaderboard", "display the anagram puzzle score leaderboard")
async def command_anagram_leaderboard(command, message):
  scores = []
  for gid, mid in default("puzzlepoints", {}):
    points = data()["puzzlepoints"][(gid, mid)].get("anagram", 0)
    if points:
      scores.append((points, message.guild.get_member(mid)))
  scores.sort(reverse = True)
  await send(message, embed = discord.Embed(
    title = "Anagram Leaderboard",
    description = "\n".join("{mention} - {score}".format(mention = member.mention, score = score) for score, member in scores) or "The leaderboard is empty!"
  ), reaction = "check")

@client.command("Reddit Commands", ["mem"], "mem", "alias for `meme`")
@client.command("Reddit Commands", ["meme"], "meme", "fetch a random meme from /r/memes")
async def command_anagram_meme(command, message):
  while True:
    meme = reddit.subreddit("memes").random()
    if message.channel.is_nsfw() or not meme.over_18:
      break
  await send(message, meme.url, reaction = "check")

@client.command("Reddit Commands", ["ket"], "ket", "alias for `cat`")
@client.command("Reddit Commands", ["cat"], "cat", "fetch a random cat image from /r/cat")
async def command_anagram_cat(command, message):
  if command[0] == "ket" and random.random() < 0.01:
    await send(message, "{mention} overdosed on ketamine and died.".format(mention = message.author.mention), reaction = "x")
  else:
    while True:
      cat = reddit.subreddit("cat").random()
      if message.channel.is_nsfw() or not cat.over_18:
        break
    await send(message, cat.url, reaction = "check")

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
        breakdown += "[ {pos} ]".format(pos = ", ".join(map(str, pos)))
      if neg:
        breakdown += " - [ {neg} ]".format(neg = ", ".join(map(str, neg)))
      if mod > 0:
        breakdown += " + {mod}".format(mod = mod)
      elif mod < 0:
        breakdown += " - {mod}".format(mod = -(mod))
      await send(message, "{mention} rolled **{result}**! ({breakdown})".format(
        mention = message.author.mention,
        result = sum(pos) - sum(neg) + mod,
        breakdown = breakdown
      ))
    else:
      await send(message, "{mention} rolled **{result}**!".format(
        mention = message.author.mention,
        result = sum(pos) - sum(neg) + mod
      ))
  else:
    await send(message, "Invalid dice configuration! The config must start with xdy (optionally +/- xdy), have zero or more +/- xdy, and optionally end with +/- a modifier.", reaction = "x")

def start():
  client.run(config["discord-tokens"]["toplane"])