"""Connection through SSH to the ReMarkable."""

import asyncio
import subprocess
from enum import Enum
from typing import Coroutine


class RemarkableModels(str, Enum):
    """Manufacturor versions of the ReMarkable"""
    V1 = "reMarkable 1.0"
    V2 = "reMarkable 2.0"

    @classmethod
    def _missing_(cls, value: object) -> None:
        raise NotImplementedError(f"Unsupported reMarkable Device : {value}")


# The ReMarkable has two inputs method outputting on two differents /dev/input:
# First with the stylus
PEN_SCREEN_DEVICE_PER_MODEL: dict[RemarkableModels, str] = {
    RemarkableModels.V1: "/dev/input/event0",
    RemarkableModels.V2: "/dev/input/event1"
}


# Second with gestures
TOUCH_SCREEN_DEVIDE_PER_MODEL: dict[RemarkableModels, str] = {
    RemarkableModels.V1: "/dev/input/event1",
    RemarkableModels.V2: "/dev/input/event2",
}


def get_remarkable_model(ssh_hostname):
    """Get the remarkable manufacturor version"""
    try:
        model = subprocess.run(
            [
                "ssh",
                "-o",
                "ConnectTimeout=2",
                ssh_hostname,
                "cat",
                "/proc/device-tree/model",
            ],
            check=True,
            capture_output=True,
        )
        return RemarkableModels(model.stdout[:14].decode("utf-8"))
    except subprocess.CalledProcessError as error:
        raise ValueError(
            f"Can't connect to reMarkable tablet on hostname : {ssh_hostname}"
        ) from error


async def get_screen_listener(device: str, ssh_hostname: str) -> Coroutine:
    """Starts a listener on a /dev/input.

    Args:
        device: the dev input to listen to
        ssh_hostname: the SSH config connection to use

    Returns:
        An asynchrone subshell ssh listener on the device
    """
    command = f"ssh -o ConnectTimeout=2 {ssh_hostname} cat {device}"

    return await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
