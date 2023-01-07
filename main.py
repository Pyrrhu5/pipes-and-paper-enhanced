import asyncio
from src.cli import cli

from src.connection import (
    PEN_SCREEN_DEVICE_PER_MODEL,TOUCH_SCREEN_DEVIDE_PER_MODEL, get_remarkable_model, get_screen_listener
)
from src.screen_api import get_screen_input, DeviceTypes, TouchEventCodes, ScreenInputEvent, EventTypes
from src.gestures import get_screen_gestures
from src.server import Websocket, run_http_server


def run_pen_debug(ssh_hostname):
    model = get_remarkable_model(ssh_hostname)
    pen_device = PEN_SCREEN_DEVICE_PER_MODEL[model]
    loop = asyncio.new_event_loop()
    pen_listener = loop.run_until_complete(
        get_screen_listener(pen_device, ssh_hostname)
    )
    print(f"Listening on {pen_device} through {ssh_hostname}")

    while not pen_listener.returncode:
        pen_screen_input = loop.run_until_complete(get_screen_input(pen_listener, DeviceTypes.PEN))
        if pen_screen_input:
            print(f"Stylus: {pen_screen_input=}")


def run_touch_debug(ssh_hostname):
    model = get_remarkable_model(ssh_hostname)
    touch_device = TOUCH_SCREEN_DEVIDE_PER_MODEL[model]
    loop = asyncio.new_event_loop()
    touch_listener = loop.run_until_complete(
        get_screen_listener(touch_device, ssh_hostname)
    )
    print(f"Listening on {touch_device} through {ssh_hostname}")

    while not touch_listener.returncode:
        gesture = loop.run_until_complete(get_screen_gestures(touch_listener))
        print(f"{gesture=}")
        if gesture.slots[list(gesture.slots.keys())[0]].x:
            print(f"X {gesture.slots[list(gesture.slots.keys())[0]].x}")

    # while not touch_listener.returncode:
    #     touch_screen_input: ScreenInputEvent = loop.run_until_complete(get_screen_input(touch_listener, DeviceTypes.TOUCH))
    #     if not touch_screen_input:
    #         continue
    #     elif touch_screen_input.code == TouchEventCodes.TRACKING_ID:
    #         print(f"End gesture: {touch_screen_input=}")
    #     else:
    #         print(f"Touch: {touch_screen_input=}")


def run_server(ssh_hostname, http_port):
    websocket_thread = Websocket(ssh_hostname=ssh_hostname)
    websocket_thread.start()
    run_http_server(http_port)


if __name__ == "__main__":
    args = cli().parse_args()
    if args.pen_debug:
        run_pen_debug(args.ssh_hostname)
    elif args.touch_debug:
        run_touch_debug(args.ssh_hostname)
    else:
        run_server(args.ssh_hostname, args.port)
