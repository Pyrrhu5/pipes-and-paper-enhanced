import asyncio
import websockets
import json
import http
import os

REMARKABLE_HOSTNAME = "remarkable"

def check():
  # Pre-emptive check, can we connect at all?
  try:
    result = subprocess.run(["ssh", "-o", "ConnectTimeout=2", REMARKABLE_HOSTNAME, "true"], check=True)
  except:
    print("Error: Can't connect to reMarkable tablet on hostname : '%s'." % REMARKABLE_HOSTNAME)
    os._exit(1)

async def websocket_handler(websocket, path):
  x = 0
  y = 0
  pressure = 0

  # The async subprocess library only accepts a string command, not a list.
  command = "ssh -o ConnectTimeout=2 %s cat /dev/input/event0" % REMARKABLE_HOSTNAME

  proc = await asyncio.create_subprocess_shell(
          command,
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE)
  print("Started process")

  try:
    # Keep looping as long as the process is alive.
    # Terminated websocket connection is handled with a throw.
    while proc.returncode == None:
      buf = await proc.stdout.read(16)

      # TODO expect 16-bit chunks, or no data.
      # There are synchronisation signals in the data stream, maybe use those
      # if we drift somehow.
      if len(buf) == 16:
        timestamp = buf[0:4]
        a = buf[4:8]
        b = buf[8:12]
        c = buf[12:16]

        # Using notes from https://github.com/ichaozi/RemarkableFramebuffer
        typ = b[0]
        code = b[2] + b[3] * 0x100
        val = c[0] + c[1] * 0x100 + c[2] * 0x10000 + c[3] * 0x1000000

        # Absolute position.
        if typ == 3:
          if code == 0:
            x = val
          elif code == 1:
            y = val
          elif code == 24:
            pressure = val

          await websocket.send(json.dumps((x,y,pressure)))
    print("Disconnected from ReMarkable.")

  finally:
    print("Disconnected from browser.")
    proc.kill()

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
