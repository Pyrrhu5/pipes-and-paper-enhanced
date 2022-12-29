import asyncio
import functools
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread

import websockets

from src.connection import (SCREEN_DEVICE_PER_MODEL, get_remarkable_model,
                            get_screen_listener)
from src.screen_api import EventCodes, EventTypes, get_screen_input


class Websocket(Thread):
    def __init__(self, remarkable_host: str, port: int = 6789, address: str = "localhost") -> None:
        self.port = port
        self.address = address
        self.remarkable_host = remarkable_host
        super().__init__(daemon=True)

    def run(self):

        model = get_remarkable_model(self.remarkable_host)
        device = SCREEN_DEVICE_PER_MODEL[model]
        partial_handler = functools.partial(
            self.handler, device=device
        )
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            websockets.serve(partial_handler, self.address, self.port)
        )
        print(
            f"Websocket ready and running on http://{self.address}:{self.port}")
        asyncio.get_event_loop().run_forever()

    async def handler(self, websocket, path, device):
        x = 0
        y = 0
        pressure = 0

        listener = await get_screen_listener(device)
        try:
            # Keep looping as long as the process is alive.
            # Terminated websocket connection is handled with a throw.
            while not listener.returncode:
                screen_input = await get_screen_input(listener)
                if not screen_input or screen_input.type != EventTypes.ABSOLUTE:
                    continue

                # TODO Replace by a proper JSON dump
                if screen_input.code == EventCodes.X:
                    x = screen_input.value
                elif screen_input.code == EventCodes.Y:
                    y = screen_input.value
                elif screen_input.code == EventCodes.PRESSURE:
                    pressure = screen_input.value
                # TODO Send it also the ERASER or TIP
                await websocket.send(json.dumps((x, y, pressure)))
            print("Disconnected from ReMarkable.")
        finally:
            listener.kill()


class HttpHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        print(f"{'='*5} {self.path} {'='*5}")
        type = "text/html"
        # Switch on path
        if self.path == "/":
            self.path = "/index.html"
        elif self.path == "/websocket":
            return None
        elif self.path.startswith("/static/js/"):
            type = "text/javascript"
        elif self.path.startswith("/static/img/"):
            type = "image/svg+xml"
        else:
            print("UNRECONGIZED REQUEST: ", self.path)
            self.path = "/404"

        if self.path != "/404":
            self.send_response(200)
        else:
            self.send_response(404)

        self.send_header("Content-type", type)
        self.end_headers()

        if self.path != "/404":
            with open(self.path[1:], 'rb') as file:
                self.wfile.write(file.read())  # Send


def run_http_server(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 8001)
    httpd = server_class(server_address, handler_class)
    print("Serving http server on http://localhost:8001")
    httpd.serve_forever()
