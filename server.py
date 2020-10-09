import subprocess
import asyncio
import websockets
import json
import threading
import queue
import http
import os

REMARKABLE_HOSTNAME = "remarkable"

def run_listen(queue):
  x = 0
  y = 0
  pressure = 0

  print("Run listen thread")

  # Pre-emptive check, can we connect at all?
  # Harder to detect at the next step when we're getting a constant stream,
  # so can't check the error code.
  try:
    result = subprocess.run(["ssh", "-o", "ConnectTimeout=2", REMARKABLE_HOSTNAME, "true"], check=True)
  except:
    print("Error: Can't connect to reMarkable tablet on hostname : '%s'." % REMARKABLE_HOSTNAME)
    os._exit(1)

  # Relies on the right setting ~/.ssh/config for hostname and public key.
  process = subprocess.Popen(
    ["ssh", REMARKABLE_HOSTNAME, "cat /dev/input/event0"],
    stdout=subprocess.PIPE)

  for buf in iter(lambda: process.stdout.read(16), b''):
    timestamp = buf[0:4]

    a = buf[4:8]
    b = buf[8:12]
    c = buf[12:16]

    # Using notes from https://github.com/ichaozi/RemarkableFramebuffer
    typ = b[0]
    code = b[2] + b[3] * 0x100
    val = c[0] + c[1] * 0x100 + c[2] * 0x10000 + c[3] * 0x1000000

    if typ == 0:
      # sync
      pass
    elif typ == 1:
      # key
      if code == 320:
        # down and up
        pass
    elif typ == 3:
      # absolute position
      # Docs have x and y as 0 and 1, but it seems to be rotated.
      # Swap the numbers here, but we have to invert in the browser.
      if code == 0:
        # X
        x = val
      elif code == 1:
        y = val

      elif code == 24:
        pressure = val

    if True:
      #print("x: %d y: %d, p: %d" % (x, y, pressure))
      queue.put((x, y, pressure))

def runner(queue):
  asyncio.run(run_listen(queue))

event_queue = queue.Queue()

# Messy mix of two threads with different async event loops.
# But the polling from the subprocess pipe is synchronous.
threading.Thread(target=runner, args=(event_queue,)).start()

async def websocket_handler(websocket, path):
        # TODO can't detect closing of websocket so if the client disconnects
        # we're still tying up the queue.
        while True:
          result = event_queue.get(block=True)
          await websocket.send(json.dumps(result))

async def http_handler(path, request):

  # only serve index file or defer to websocket handler.
  if path == "/websocket":
    return None
  elif path != "/":
    return (http.HTTPStatus.NOT_FOUND, [], "")

  body = open("index.html", "rb").read()
  headers = [("Content-Type", "text/html"),
             ("Content-Length", str(len(body))),
             ("Connection", "close")]

  return (http.HTTPStatus.OK, headers, body)

PORT = 6789
HOST = "localhost"

start_server = websockets.serve(websocket_handler,
                                "localhost",
                                6789,
                                ping_interval=1000,
                                process_request=http_handler)

print("Visit http://%s:%d/" % (HOST, PORT))

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
