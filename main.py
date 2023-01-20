import asyncio
from src.cli import cli

from src.connection import (SCREEN_DEVICE_PER_MODEL, get_remarkable_model,
                            get_screen_listener)
from src.screen_api import get_screen_input
from src.server import Websocket, run_http_server


def run_debug(ssh_hostname, ssh_password):
    model = get_remarkable_model(ssh_hostname, ssh_password)
    device = SCREEN_DEVICE_PER_MODEL[model]
    loop = asyncio.new_event_loop()
    listener = loop.run_until_complete(
        get_screen_listener(device, ssh_hostname, ssh_password))
    print(f"Listening on {device} through {ssh_hostname}")

    while not listener.returncode:
        screen_input = loop.run_until_complete(get_screen_input(listener))
        if not screen_input:
            continue
        print(f"{screen_input=}")


def run_server(ssh_hostname, ssh_password, http_port):
    websocket_thread = Websocket(ssh_hostname=ssh_hostname, ssh_password=ssh_password)
    websocket_thread.start()
    run_http_server(http_port)


if __name__ == "__main__":
    args = cli().parse_args()
    print(args)
    if args.screen_debug:
        run_debug(args.ssh_hostname, args.ssh_password)
    else:
        run_server(args.ssh_hostname, args.ssh_password, args.port)
