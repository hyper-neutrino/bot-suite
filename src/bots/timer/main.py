import asyncio, base64, discord, requests, time, traceback

from utils.datautils import config, set_client
from utils.discordbot import BotClient, send

client = None

class TimerClient(BotClient):
  def __init__(self):
    BotClient.__init__(self, "timer")
    self.name = "timer"

client = TimerClient()

@client.command("Testing Commands", ["test"], "test", "Test the Timer bot")
async def command_test(command, message):
  await send(message, "Test success!", reaction = "check")

@client.command("Timer Commands", ["start"], "start", "Start a standard 5-minute BP timer")
async def command_start(command, message):
  replies = []
  replies.append(await send(message, "5-minute timer started!", reaction = "check"))
  await asyncio.sleep(30)
  replies.append(await send(message, "Protected time over!"))
  await asyncio.sleep(30)
  replies.append(await send(message, "4 minutes remaining!"))
  await asyncio.sleep(60)
  replies.append(await send(message, "3 minutes remaining!"))
  await asyncio.sleep(60)
  replies.append(await send(message, "2 minutes remaining!"))
  await asyncio.sleep(60)
  replies.append(await send(message, "1 minute remaining!"))
  await asyncio.sleep(30)
  replies.append(await send(message, "Protected time!"))
  await asyncio.sleep(30)
  replies.append(await send(message, "15-second grace period!"))
  await asyncio.sleep(5)
  replies.append(await send(message, "10 seconds!"))
  await asyncio.sleep(5)
  replies.append(await send(message, "5 seconds!"))
  await asyncio.sleep(5)
  replies.append(await send(message, "Time's Up!"))
  await asyncio.sleep(5)
  await send(message, "[a 5-minute timer was run]")
  await message.channel.delete_messages(replies)

set_client(client)

def start():
  client.run(config["discord-tokens"]["timer"])