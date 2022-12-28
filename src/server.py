import http
import json


from src.connection import get_screen_listener
from src.screen_api import EventCodes, EventTypes, get_screen_input

async def websocket_handler(websocket, device):

    # The async subprocess library only accepts a string command, not a list.

    x = 0
    y = 0
    pressure = 0

    listener = await get_screen_listener(device)
    try:
        # Keep looping as long as the process is alive.
        # Terminated websocket connection is handled with a throw.
        while not listener.returncode:
            screen_input = await get_screen_input(listener)
            if not screen_input  or screen_input.type != EventTypes.ABSOLUTE: 
                continue

            #TODO Replace by a proper JSON dump
            if screen_input.code == EventCodes.X:
                x = screen_input.value
            elif screen_input.code == EventCodes.Y:
                y = screen_input.value
            elif screen_input.code == EventCodes.PRESSURE:
                pressure = screen_input.value


            #TODO Send it also the ERASER or TIP
            await websocket.send(json.dumps((x, y, pressure)))
        print("Disconnected from ReMarkable.")

    finally:
        print("Disconnected from browser.")
        listener.kill()


async def http_handler(path, request):
    # only serve index file or defer to websocket handler.
    if path == "/websocket":
        return None

    elif path != "/":
        return (http.HTTPStatus.NOT_FOUND, [], "")

    body = open("index.html", "rb").read()
    headers = [
        ("Content-Type", "text/html"),
        ("Content-Length", str(len(body))),
        ("Connection", "close"),
    ]

    return (http.HTTPStatus.OK, headers, body)

