import asyncio, base64, discord, requests, time, traceback

from utils.datautils import config, set_client
from utils.discordbot import BotClient, send

client = None

class TimerClient(BotClient):
  def __init__(self):
    BotClient.__init__(self, "")
    self.name = "timer"

client = TimerClient()

timers = {}

@client.command("Timer Commands", ["-start"], "-start", "Start a 5-minute BP timer; 30 seconds protected time, 15 seconds grace.")
async def command_start(command, message):
  cid = message.channel.id
  mid = message.id
  timers[cid] = timers.get(cid, []) + [mid]
  replies = []
  replies.append(await send(message, "5-minute timer started!", reaction = "check"))
  await asyncio.sleep(30)
  if mid in timers[cid]: replies.append(await send(message, "Protected time over!"))
  await asyncio.sleep(30)
  if mid in timers[cid]: replies.append(await send(message, "4 minutes remaining!"))
  await asyncio.sleep(60)
  if mid in timers[cid]: replies.append(await send(message, "3 minutes remaining!"))
  await asyncio.sleep(60)
  if mid in timers[cid]: replies.append(await send(message, "2 minutes remaining!"))
  await asyncio.sleep(60)
  if mid in timers[cid]: replies.append(await send(message, "1 minute remaining!"))
  await asyncio.sleep(30)
  if mid in timers[cid]: replies.append(await send(message, "Protected time!"))
  await asyncio.sleep(30)
  if mid in timers[cid]: replies.append(await send(message, "15-second grace period!"))
  await asyncio.sleep(5)
  if mid in timers[cid]: replies.append(await send(message, "10 seconds!"))
  await asyncio.sleep(5)
  if mid in timers[cid]: replies.append(await send(message, "5 seconds!"))
  await asyncio.sleep(5)
  if mid in timers[cid]: replies.append(await send(message, "Time's Up!"))
  await asyncio.sleep(5)
  if mid in timers[cid]: await send(message, "[a 5-minute timer was run]")
  if mid in timers[cid]: await message.channel.delete_messages(replies)

@client.command("Timer Commands", ["-stop"], "-stop", "Stops all timers in this channel.")
async def command_stop(command, message):
  timers[message.channel.id] = []
  await send(message, "All timers in this channel stopped!", reaction = "check")

set_client(client)