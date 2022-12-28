"""Connection through SSH to the ReMarkable."""

import asyncio
from enum import Enum
import subprocess

class RemarkableModels(str, Enum):
    V1 = "reMarkable 1.0"
    V2 = "reMarkable 2.0"

    @classmethod
    def _missing_(cls, value: object) -> None:
        raise NotImplementedError(f"Unsupported reMarkable Device : {value}")


SCREEN_DEVICE_PER_MODEL: dict[RemarkableModels, str] = {
    RemarkableModels.V1: "/dev/input/event0",
    RemarkableModels.V2: "/dev/input/event1"
}


def get_remarkable_model(ssh_hostname):
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
    except subprocess.CalledProcessError:
        raise ValueError(f"Can't connect to reMarkable tablet on hostname : {ssh_hostname}")


async def get_screen_listener(device: str):
    command = f"ssh -o ConnectTimeout=2 rem cat {device}"

    return await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

