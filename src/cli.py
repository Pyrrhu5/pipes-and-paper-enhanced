"""Command line interface setup."""
from argparse import ArgumentParser


def cli() -> ArgumentParser:

    parser = ArgumentParser(
        description="Screen share in browser for ReMarkable tablets."
    )
    parser.add_argument(
        "-p", "--port",
        default=8001,
        type=int,
        help="The port to use to expose the website on localhost."
    )
    parser.add_argument(
        "-s", "--ssh-hostname",
        default="rem",
        dest="ssh_hostname",
        help="The name of the ReMarkable SSH host."
    )
    parser.add_argument(
        "--pen-debug",
        action="store_true",
        dest="pen_debug",
        help="Instead of running the web server, run in stylus input debug mode."
    )
    parser.add_argument(
        "--touch-debug",
        action="store_true",
        dest="touch_debug",
        help="Instead of running the web server, run in touch input debug mode."
    )

    return parser
