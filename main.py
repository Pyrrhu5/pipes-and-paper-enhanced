
import asyncio
import functools

import threading
import websockets

from src.connection import SCREEN_DEVICE_PER_MODEL, get_remarkable_model, get_screen_listener
from src.screen_api import get_screen_input
from src.server import http_handler, run_http_server, websocket_handler


def run_debug():
    model = get_remarkable_model("rem")
    device = SCREEN_DEVICE_PER_MODEL[model]
    loop = asyncio.new_event_loop()
    listener = loop.run_until_complete(get_screen_listener(device))
    print(f"Listening on {device}")

    while not listener.returncode:
        screen_input = loop.run_until_complete(get_screen_input(listener))
        if not screen_input: # or screen_input.type != EventTypes.ABSOLUTE: 
            continue
        print(f"{screen_input=}")


def run_server(rm_host="rem", host="localhost", port=6789):
    model = get_remarkable_model(rm_host)
    device = SCREEN_DEVICE_PER_MODEL[model]

    print(f"Listening on {device}")

    bound_handler = functools.partial(
        websocket_handler, device=device 
    )
    http_thread = threading.Thread(target=run_http_server)
    http_thread.start()
    start_server = websockets.serve(
        bound_handler, host, port, ping_interval=1000, process_request=http_handler
    )

    print(f"Visit http://{host}:{port}/")

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    # run_debug()
    run_server()
