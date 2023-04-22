import asyncio
from time import sleep
from typing import Union, List
from dataclasses import dataclass
from enum import Enum
import functools
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from threading import Thread

import websockets

from src.connection import (SCREEN_DEVICE_PER_MODEL, get_remarkable_model,
                            get_screen_listener)
from src.screen_api import EventCodes, EventTypes, get_screen_input


def websocket_payload(payload_type, message: List[Union[Enum, tuple]]):
    payload = {"type": payload_type}
    if isinstance(message, dict):
        payload["message"] = message
    elif not len(message):
        ...
    elif isinstance(message[0], Enum):
        payload["message"] = {
            m.name: m.value
            for m in message
        }
    return json.dumps(payload)


class Websocket(Thread):
    def __init__(self, ssh_hostname: str, port: int = 6789, address: str = "localhost") -> None:
        self.port = port
        self.address = address
        self.ssh_hostname = ssh_hostname
        super().__init__(daemon=True)

    def run(self):

        model = None
        while not model:
            try:
                model = get_remarkable_model(self.ssh_hostname)
            except Exception:
                print(
                    f"Can cannot connect to ReMarkable on {self.ssh_hostname}. Retrying..."
                )
                sleep(0.5)
        device = SCREEN_DEVICE_PER_MODEL[model]
        partial_handler = functools.partial(
            self.handler, device=device, ssh_hostname=self.ssh_hostname
        )
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            websockets.serve(partial_handler, self.address, self.port)
        )
        print(
            f"Websocket ready and running on http://{self.address}:{self.port}")
        asyncio.get_event_loop().run_forever()

    async def handler(self, websocket, path, device, ssh_hostname):
        x = 0
        y = 0
        pressure = 0

        listener = await get_screen_listener(device, ssh_hostname)
        try:
            # Keep looping as long as the process is alive.
            # Terminated websocket connection is handled with a throw.
            while not listener.returncode:
                screen_input = await get_screen_input(listener)

                if not screen_input:
                    continue
                # It's sending coordinates
                elif screen_input.type == EventTypes.ABSOLUTE:
                    if screen_input.code == EventCodes.X:
                        x = screen_input.value
                    elif screen_input.code == EventCodes.Y:
                        y = screen_input.value
                    elif screen_input.code == EventCodes.PRESSURE:
                        pressure = screen_input.value
                    await websocket.send(websocket_payload("coordinates", {"x": x, "y": y, "pressure": pressure}))
                # It's sending tool used
                elif screen_input.type == EventTypes.KEY and screen_input.code in (EventCodes.ERASER, EventCodes.TIP):
                    await websocket.send(websocket_payload("tool", [screen_input.code]))
            print("Disconnected from ReMarkable.")
        finally:
            listener.kill()


class HttpHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        type = "text/html"
        # Switch on path
        if self.path == "/":
            self.path = "/index.html"
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


def run_http_server(port: int, server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Serving http server on http://localhost:{port}")
    httpd.serve_forever()
