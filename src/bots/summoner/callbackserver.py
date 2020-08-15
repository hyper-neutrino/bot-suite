import base64

from aiohttp import web

from .bot import announce

from utils.datautils import config

app = web.Application()

names = {
  "toplane": "TopLane",
  "jungler": "Jungler",
  "midlane": "MidLane",
  "botlane": "BotLane",
  "support": "Support"
}

async def process(request):
  bot = request.query["bot"]
  botname = names[bot]
  stat = base64.b64decode(bytes(request.query["value"], "utf-8")).decode("utf-8")
  if stat == "READY":
    pass # await announce("{name} is ready!".format(name = botname))
  elif stat == "CONNECT":
    pass # await announce("{name} has connected!".format(name = botname))
  elif stat == "DISCONNECT":
    pass # await announce("{name} has disconnected!".format(name = botname))
  return web.Response(text = "success")

app.add_routes([
  web.get("/", process)
])

async def start_server():
  runner = web.AppRunner(app)
  await runner.setup()
  site = web.TCPSite(runner, "127.0.0.1", config["global-arguments"]["callback-port"])
  await site.start()