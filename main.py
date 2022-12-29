
import asyncio
import functools

import threading

from src.connection import SCREEN_DEVICE_PER_MODEL, get_remarkable_model, get_screen_listener
from src.screen_api import get_screen_input
from src.server import run_http_server, Websocket

def run_debug():
    model = get_remarkable_model("rem")
    device = SCREEN_DEVICE_PER_MODEL[model]
    loop = asyncio.new_event_loop()
    listener = loop.run_until_complete(get_screen_listener(device))
    print(f"Listening on {device}")

    while not listener.returncode:
        screen_input = loop.run_until_complete(get_screen_input(listener))
        if not screen_input:
            continue
        print(f"{screen_input=}")


def run_server():
    websocket_thread = Websocket(remarkable_host="rem")
    websocket_thread.start()
    run_http_server()

if __name__ == "__main__":
    # run_debug()
    run_server()
