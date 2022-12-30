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
        "--screen-debug",
        action="store_true",
        dest="screen_debug",
        help="Instead of running the web server, run in screen input debug mode."
    )

    return parser
