import base64, discord, hashlib, math, os, requests, time, traceback, youtube_dl

from discord.utils import get

from utils.datautils import config, data, default, discard, save_data, set_client
from utils.discordbot import BotClient, emoji_shorthand, send
from utils.errors import BotError
from utils.logging import log

client = None

downloader = youtube_dl.YoutubeDL({
  "format": "bestaudio/best"
})

def gfn(vid):
  return "music/" + hashlib.md5(bytes(vid, "utf-8")).hexdigest() + ".webm"

def cutmax(string, length, term = "..."):
  if len(string) > length:
    return string[:length - len(term)] + term
  return string

class BotlaneClient(BotClient):
  def __init__(self):
    BotClient.__init__(self)
    self.name = "botlane"

client = BotlaneClient()

histories = {}
queues = {}
nowplaying = {}
stopskip = {}
playtime = {}
timetrack = {}

def current(gid, key, default = "<unknown>"):
  return nowplaying.get(gid, {}).get(key, default)

def gettime(voice, gid):
  if voice.is_paused():
    return playtime[gid]
  elif voice.is_playing():
    return playtime[gid] + time.time() - timetrack[gid]
  else:
    return 0

def ftime(seconds):
  seconds = int(seconds)
  if seconds < 60:
    return f"0:{str(seconds).zfill(2)}"
  elif seconds < 3600:
    return f"{seconds // 60}:{str(seconds % 60).zfill(2)}"
  else:
    return f"{seconds // 3600}:{str(seconds % 3600 // 60).zfill(2)}:{str(seconds % 60).zfill(2)}"

@client.command("Testing Commands", ["test"], "test", "Test the BotLane bot")
async def command_test(command, message):
  await send(message, "Test success!", reaction = "check")

@client.command("Voice Commands", ["join"], "join", "join your voice channel")
async def command_join(command, message):
  if message.author.voice:
    channel = message.author.voice.channel
    voice = get(client.voice_clients, guild = message.guild)
    if voice and voice.is_connected():
      await voice.move_to(channel)
    else:
      voice = await channel.connect()
    await send(message, f"Connected to {channel.name}!", reaction = "check")
  else:
    await send(message, "You must be in a voice channel to use the `join` command!", reaction = "x")

@client.command("Voice Commands", ["leave"], "leave", "leave the current voice channel (purges the queue and history)")
async def command_leave(command, message):
  voice = get(client.voice_clients, guild = message.guild)
  if voice and voice.is_connected():
    await voice.disconnect()
    discard(queues, message.guild.id)
    discard(histories, message.guild.id)
    discard(stopskip, message.guild.id)
    discard(nowplaying, message.guild.id)
    await send(message, "Disconnected!", reaction = "check")
  else:
    await send(message, "I am not connected to a voice channel!", reaction = "x")

async def get_voice(message):
  voice = get(client.voice_clients, guild = message.guild)
  if message.author.id in config["global-arguments"]["sudo"] or message.author.voice:
    if voice and voice.is_connected():
      if message.author.id in config["global-arguments"]["sudo"] or voice.channel == message.author.voice.channel:
        return voice
      else:
        raise BotError("You must be in the same channel as me to use this command!")
    else:
      return await message.author.voice.channel.connect()
  else:
    raise BotError("You must be connected to a voice channel to use this command!")

@client.command("Voice Commands", ["playshuffle", ".+"], "play <url>", "same as `play` but inserts songs shuffled (if called on a playlist; otherwise, it is the exact same as `play`)")
@client.command("Voice Commands", ["play", ".+"], "play <url>", "play audio from YouTube (appends a song to the queue if playing, and places at the front if not)")
async def command_play(command, message):
  voice = await get_voice(message)
  try:
    info = downloader.extract_info(command[1], download = False)
    queue = await default(message.guild.id, [], queues)
    if voice.is_playing():
      queue.append((command[1], info, message.author))
      embed = discord.Embed(
        title = "Added to Queue!",
        description = f"[**{info['title']}**]({command[1]})",
        color = 0x3333AA
      ).add_field(
        name = "Channel",
        value = f"[{info['uploader']}]({info['uploader_url']})"
      ).add_field(
        name = "Song Length",
        value = ftime(info["duration"])
      )
      if info["thumbnails"]:
        embed.set_thumbnail(url = info["thumbnails"][-1]["url"])
      await send(message, embed = embed, reaction = "check")
    else:
      queue.insert(0, (command[1], info, message.author))
      await playaudio(message.channel)
      await message.add_reaction(emoji_shorthand["check"])
  except:
    print(traceback.format_exc())
    await send(message, f"Invalid URL: `{command[1]}`!", reaction = "x")

@client.command("Voice Commands", ["stop"], "stop", "stops the player (places the current song into history but retains the remaining queue)")
async def command_stop(command, message):
  voice = await get_voice(message)
  if voice.is_playing() or voice.is_paused():
    queue = await default(message.guild.id, [], queues)
    if len(queue) > 0:
      (await default(message.guild.id, [], histories)).append(queue.pop(0))
    stopskip[message.guild.id] = stopskip.get(message.guild.id, 0) + 1
    voice.stop()
  if not await default(message.guild.id, [], queues):
    await send(message, "Nothing is playing!", reaction = "x")
  if message.guild.id in nowplaying:
    del nowplaying[message.guild.id]
  await send(message, "Stopped the player!", reaction = "check")

@client.command("Voice Commands", ["pause"], "pause", "pauses the player")
async def command_pause(command, message):
  voice = await get_voice(message)
  if voice.is_paused():
    await send(message, "Already paused!", reaction = "x")
  elif not voice.is_playing():
    await send(message, "Nothing is playing!", reaction = "x")
  else:
    voice.pause()
    playtime[message.guild.id] += time.time() - timetrack[message.guild.id]
    await send(message, "Paused!", reaction = "check")

@client.command("Voice Commands", ["play"], "play", "alias for `resume` (if not called with a URL)")
@client.command("Voice Commands", ["resume"], "resume", "resume the player if it is paused; start playing from the queue if it is stopped")
async def command_pause(command, message):
  voice = await get_voice(message)
  if voice.is_paused():
    voice.resume()
    timetrack[message.guild.id] = time.time()
    await send(message, "Resumed!", reaction = "check")
  elif voice.is_playing():
    await send(message, "Player is not currently paused!", reaction = "x")
  elif await default(message.guild.id, [], queues):
    await playaudio(message.channel)
  else:
    await send(message, "Nothing is playing and the queue is empty!", reaction = "x")

@client.command("Voice Commands", ["backtrack", "?"], "backtrack [amount = 1]", "backtrack to a song / songs in the history and start playing the new song (least recent song first)")
@client.command("Voice Commands", ["skip", "?"], "skip [amount = 1]", "skip a song / songs and start playing the next song in the queue if present")
async def command_skip(command, message):
  try:
    amt = int(command[1]) if len(command) > 1 else 1
  except:
    print(traceback.format_exc())
    await send(message, "Not an integer!", reaction = "x")
    amt = None
  if amt is not None:
    if amt <= 0:
      await send(message, "Must be a positive integer!", reaction = "x")
    else:
      voice = await get_voice(message)
      gid = message.guild.id
      queue = await default(gid, [], queues)
      history = await default(gid, [], histories)
      if command[0] == "skip":
        history.extend(queue[:amt])
        queue[:amt] = []
        await send(message, f"Skipped `{current(gid, 'title')}`!" if amt == 1 else f"Skipped {amt} songs!", reaction = "check")
      else:
        queues[gid] = history[-amt:] + queue
        history[-amt:] = []
        await send(message, f"Backtracked {amt} song{'' if amt == 1 else 's'}!", reaction = "check")
      if voice.is_playing() or voice.is_paused():
        stopskip[message.guild.id] = stopskip.get(message.guild.id, 0) + 1
        voice.stop()
      await playaudio(message.channel)

@client.command("Voice Commands", ["replay"], "replay", "start playing the current song from the beginning")
async def command_replay(command, message):
  voice = await get_voice(message)
  if voice.is_playing() or voice.is_paused():
    stopskip[message.guild.id] = stopskip.get(message.guild.id, 0) + 1
    voice.stop()
    await send(message, f"Restarting `{current(message.guild.id, 'title')}`!", reaction = "check")
    await playaudio(message.channel)
  else:
    await send(message, "Nothing is playing!", "x")

@client.command("Voice Commands", ["np"], "np", "alias for `nowplaying`")
@client.command("Voice Commands", ["nowplaying"], "nowplaying", "display the current song")
async def command_queue(command, message):
  if not queues.get(message.guild.id):
    await send(message, "Nothing is playing in this server!", reaction = "x")
  else:
    voice = await get_voice(message)
    url, info, user = queues[message.guild.id][0]
    ct = gettime(voice, message.guild.id)
    prog = int(29 * ct / info["duration"])
    bar = "▬" * prog + ("⏸️" if voice.is_paused() else "🔘") + "▬" * (29 - prog)
    await send(message, embed = discord.Embed(
      title = f"Now Playing in {message.guild.name}",
      description = f"""[{cutmax(info['title'], 85)}]({url})
by [{cutmax(info['uploader'], 85)}]({info['uploader_url']})

`{bar}`

{ftime(gettime(voice, message.guild.id))} / {ftime(info['duration'])}

Requested by: {user.mention}""",
      color = 0x3333AA
    ), reaction = "check")

@client.command("Voice Commands", ["history", "?"], "history [page = 1]", "display the song history")
@client.command("Voice Commands", ["queue", "?"], "queue [page = 1]", "display the song queue")
async def command_queue(command, message):
  itemmap = histories if command[0] == "history" else queues
  try:
    page = int(command[1]) if len(command) > 1 else 1
  except:
    await send(message, "Page must be an integer!", reaction = "x")
    page = None
  if page is not None:
    if page <= 0:
      await send(message, "Page must be a positive integer!", reaction = "x")
    else:
      page -= 1
      mv = 0 if command[0] == "history" else 1
      if len(await default(message.guild.id, [], itemmap)) < mv:
        await send(message, "Nothing is in the history (has finished playing) in this server! (this message should actually never occur)" if command[0] == "history" else "Nothing is playing in this server!", reaction = "x")
      else:
        voice = await get_voice(message)
        items = itemmap[message.guild.id]
        url, info, user = queues[message.guild.id][0]
        msg = f"""__Now Playing__
    [{cutmax(info['title'], 85)}]({url})
    by [{cutmax(info['uploader'], 85)}]({info['uploader_url']})
    `{ftime(gettime(voice, message.guild.id))} / {ftime(info['duration'])}` Requested by: {user.mention}

    __Song {'History (most recent song first)' if command[0] == 'history' else 'Queue'}__
    """
        if len(items) > mv:
          maxpages = int(math.ceil((len(items) - mv) / 10))
          if page >= maxpages:
            msg += f"There are only {maxpages} pages of songs in the {command[0]}!" if maxpages == 1 else f"There is only 1 page of songs in the {command[0]}!"
          else:
            for pos, (url, info, user) in enumerate(items[::-1 if command[0] == "history" else 1][page * 10 + mv:][:10]):
              msg += f"{page * 10 + pos + 1}. [{cutmax(info['title'], 85)}]({url}) | by [{cutmax(info['uploader'], 85)}]({info['uploader_url']})\n`{ftime(info['duration'])}` Requested by: {user.mention}\n\n"
            msg += f"Page {page + 1}/{maxpages}"
        else:
          msg += "No songs have finished playing yet!" if command[0] == "history" else "No more songs are queued!"
        
        await send(message, embed = discord.Embed(title = f"{'History' if command[0] == 'history' else 'Queue'} for {message.guild.name}", description = msg, color = 0x3333AA), reaction = "check")

@client.command("", ["testsongs"], "", "")
async def command_testsongs(command, message):
  await send(message, "please play https://www.youtube.com/watch?v=Zasx9hjo4WY")
  await send(message, "please play https://www.youtube.com/watch?v=GMG-SkU0Cis")
  await send(message, "please play https://www.youtube.com/watch?v=UOxkGD8qRB4")
  await send(message, "please play https://www.youtube.com/watch?v=4Twd965VzX4")

@client.command("", ["stat"], "", "")
async def command_stat(command, message):
  await send(message, str(histories.get(message.guild.id)))
  await send(message, str(queues.get(message.guild.id)))
  await send(message, f"`{nowplaying.get(message.guild.id, {'title':'None'})['title']}`")
  await send(message, str(stopskip.get(message.guild.id)))

async def playaudio(channel):
  gid = channel.guild.id
  voice = get(client.voice_clients, guild = channel.guild)
  queue = await default(gid, [], queues)
  
  if voice is None:
    log("PlayAudio invoked without being connected!", "WARN")
    return
  
  if voice.is_playing() or voice.is_paused():
    voice.stop()
  else:
    if len(queue) == 0:
      log("PlayAudio invoked without any items left in the queue, so exiting!", "WARN")
      return

    fn = gfn(queue[0][1]["id"])

    youtube_dl.YoutubeDL({
      "format": "bestaudio/best",
      "outtmpl": fn
    }).download([queue[0][0]])

    if not os.path.isfile(fn):
      log(f"PlayAudio didn't generate the expected audio file {fn}!", "ERROR")
      return
  
    nowplaying[channel.guild.id] = queue[0][1]

    voice.play(discord.FFmpegPCMAudio(fn), after = lambda e: client.loop.create_task(postplay(channel, e)))
    voice.source = discord.PCMVolumeTransformer(voice.source)
    voice.source.volume = 1
    
    playtime[channel.guild.id] = 0
    timetrack[channel.guild.id] = time.time()

    embed = discord.Embed(
      title = "Now Playing!",
      description = f"[**{queue[0][1]['title']}**]({queue[0][0]})",
      color = 0x3333AA
    ).add_field(
      name = "Channel",
      value = f"[{queue[0][1]['uploader']}]({queue[0][1]['uploader_url']})"
    ).add_field(
      name = "Song Length",
      value = ftime(queue[0][1]["duration"])
    )
    if queue[0][1]["thumbnails"]:
      embed.set_thumbnail(url = queue[0][1]["thumbnails"][-1]["url"])
    await channel.send(embed = embed)
  
async def postplay(channel, error):
  print(f"Done playing in {channel.guild.name}#{channel.name}")
  if error:
    await channel.send(f"Song ended with an error: {error}")
  if stopskip.get(channel.guild.id, 0) > 0:
    stopskip[channel.guild.id] -= 1
  else:
    queue = await default(channel.guild.id, [], queues)
    if len(queue) > 0:
      (await default(channel.guild.id, [], histories)).append(queue.pop(0))
    await playaudio(channel)

set_client(client)