import asyncio
import functools
import http
import json
import os
import subprocess

import websockets


def check(rm_hostname):
    try:
        model = subprocess.run(
            [
                "ssh",
                "-o",
                "ConnectTimeout=2",
                rm_hostname,
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
    command = f"ssh -o ConnectTimeout=2 {rm_host} cat {device}"

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
                # or https://github.com/canselcik/libremarkable/wiki
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
