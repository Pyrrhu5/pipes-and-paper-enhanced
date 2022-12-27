import asyncio
import functools
import http
import json
import os
import subprocess

import websockets

from screen_api import EventCodes, EventTypes, get_screen_input


def check(rm_hostname):
    try:
        model = subprocess.run(
            [
                "ssh",
                "-o",
                "ConnectTimeout=2",
                "rem",
                "cat",
                "/proc/device-tree/model",
            ],
            check=True,
            capture_output=True,
        )
        return model.stdout[:14].decode("utf-8")
    except subprocess.CalledProcessError:
        print(f"Error: Can't connect to reMarkable tablet on hostname : {rm_hostname}")
        os._exit(1)


async def websocket_handler(websocket, path, rm_host, rm_model):
    if rm_model == "reMarkable 1.0":
        device = "/dev/input/event0"
    elif rm_model == "reMarkable 2.0":
        device = "/dev/input/event1"
    else:
        raise NotImplementedError(f"Unsupported reMarkable Device : {rm_model}")

    # The async subprocess library only accepts a string command, not a list.
    command = f"ssh -o ConnectTimeout=2 rem cat {device}"

    x = 0
    y = 0
    pressure = 0

    proc = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    print("Started process")

    try:
        # Keep looping as long as the process is alive.
        # Terminated websocket connection is handled with a throw.
        while proc.returncode == None:
            screen_input = await get_screen_input(proc)
            if not screen_input: # or screen_input.type != EventTypes.ABSOLUTE: 
                continue

            #TODO Replace by a proper JSON dump
            if screen_input.code == EventCodes.X:
                x = screen_input.value
            elif screen_input.code == EventCodes.Y:
                y = screen_input.value
            elif screen_input.code == EventCodes.PRESSURE:
                pressure = screen_input.value
            elif screen_input.code == EventCodes.UNKNOWN:
                print(f"{screen_input=}")


            #TODO Send it also the ERASER or TIP
            await websocket.send(json.dumps((x, y, pressure)))
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
    headers = [
        ("Content-Type", "text/html"),
        ("Content-Length", str(len(body))),
        ("Connection", "close"),
    ]

    return (http.HTTPStatus.OK, headers, body)


def run(rm_host="remarkable", host="localhost", port=6789):
    rm_model = check(rm_host)
    bound_handler = functools.partial(
        websocket_handler, rm_host=rm_host, rm_model=rm_model
    )
    start_server = websockets.serve(
        bound_handler, host, port, ping_interval=1000, process_request=http_handler
    )

    print(f"Visit http://{host}:{port}/")

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    run()
