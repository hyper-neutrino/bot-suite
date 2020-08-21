import base64, discord, os, requests

from discord.utils import get

from utils.datautils import config, data, default, save_data, set_client
from utils.discordbot import BotClient, send

client = None

class BotlaneClient(BotClient):
  def __init__(self):
    BotClient.__init__(self)
    self.name = "botlane"

client = BotlaneClient()

voices = {}
queues = {}

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

@client.command("Voice Commands", ["leave"], "leave", "leave the current voice channel")
async def command_leave(command, message):
  voice = get(client.voice_clients, guild = message.guild)
  if voice and voice.is_connected():
    await voice.disconnect()
    await send(message, "Disconnected!", reaction = "check")
  else:
    await send(message, "I am not connected to a voice channel!", reaction = "x")

@client.command("Voice Commands", ["play", ".+"], "play <url>", "play audio from YouTube")
async def command_play(command, message):
  queue = default(message.guild.id, [], queues)

set_client(client)

def start():
  client.run(config["discord-tokens"]["botlane"])