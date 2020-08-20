import pickle

from flask import Flask
from flask_cors import CORS

from filelock import FileLock

app = Flask(__name__)
CORS(app)

lock = FileLock("data.pickle.lock")

@app.route("/collapse/<id>")
def serve_collapse(id):
  with lock:
    with open("data.pickle", "rb") as f:
      data = pickle.load(f)
      if "collapse" not in data or id not in data["collapse"]:
        return "404 - collapsed data link not found; probably report this to alex.yj.liao@gmail.com unless you typed this manually in which case... why?", 404
      return '<div style="font-family:monospace;font-size:150%"><h3>Collapsed Messages</h3><ul>' + "".join("<li>[{user}] {message}</li>".format(
        user = user,
        message = message
      ) for user, message in data["collapse"][id]) + '</ul></div>'

if __name__ == "__main__":
  app.run(host = "0.0.0.0", port = 5252)