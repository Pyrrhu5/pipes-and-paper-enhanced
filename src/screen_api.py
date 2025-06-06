from __future__ import annotations

from asyncio.subprocess import Process
from dataclasses import dataclass
from enum import Enum
from json import dumps
from struct import unpack
from typing import Optional, Union

from src.connection import RemarkableModels


class EventTypes(int, Enum):
    """Type of events."""
    SYNC = 0
    KEY = 1  # Represents the interaction tool (?) like the pen used
    RELATIVE = 2
    ABSOLUTE = 3  # Represents data on the screen in absolute value


class EventCodes(int, Enum):
    """Which data point the value is a reference of, returns cls.UNKNOWN as a default.

    Mixes codes from EventTypes.ABSOLUTE and EventTypes.KEY (and probably also the others in UNKNOWN)
    """

    # Happens with EventTypes.ABSOLUTE
    X = 0
    Y = 1
    PRESSURE = 24
    DISTANCE = 25  # Distance of the pen from the screen
    TILT_X = 27
    TILT_Y = 26

    # Happens with EventTypes.KEY
    TIP = 320  # When the tip of the pen is used
    ERASER = 321  # When the eraser of the pen is used
    ENGAGE = 330  # When the pen leaves or enters the detection zone

    # Default value for unknown codes
    UNKNOWN = -1

    @classmethod
    def _missing_(cls, value: str) -> EventCodes:
        """Provides a fallback value for unrepresented values to cls.UNKNOWN"""
        print(f"{cls} can not represent {value}. Defaulting to {cls.UNKNOWN}")
        return cls.UNKNOWN


@dataclass
class ScreenInputEvent:
    """Represent the data contained in a screen event payload."""
    timestamp: float
    type: EventTypes
    code: EventCodes
    value: Union[int, bool]

    @property
    def __dict__(self):
        return {
            "timestamp": self.timestamp,
            "type": self.type.name.lower(),
            "code": self.code.name.lower(),
            "value": self.value
        }

    @property
    def json(self):
        return dumps(self.__dict__)


def decode_screen_event(model: RemarkableModels, buffer: bytes) -> ScreenInputEvent:
    """Decode the bytes received from the screen events.

    Some part of the buffer are not decoded:
        buffer[4:8]

    See:
        https://github.com/ichaozi/RemarkableFramebuffer
        https://github.com/canselcik/libremarkable
    """

    if model in [RemarkableModels.V1, RemarkableModels.V2]:
        (timestamp,
         _,
         type,
         code,
         value,
        ) = unpack("<fiHHi", buffer)
    elif model == RemarkableModels.PP:
        (seconds,
         subseconds,
         type,
         code,
         value,
        ) = unpack("<QQHHi", buffer)

        timestamp = seconds + subseconds / 1000000
    else:
        raise NotImplementedError()

    return ScreenInputEvent(
        timestamp=timestamp,
        type=type,
        code=code,
        value=value,
    )


async def get_screen_input(model, subprocess_shell: Process) -> Optional[ScreenInputEvent]:
    if model in [RemarkableModels.V1, RemarkableModels.V2]:
        packet_size = 16
    elif model == RemarkableModels.PP:
        packet_size = 24
    else:
        raise NotImplementedError()

    buffer: bytes = await subprocess_shell.stdout.read(packet_size)

    if len(buffer) != packet_size:
        raise ValueError(f"Buffer is not {packet_size} bytes: {len(buffer)=} {buffer=}")

    return decode_screen_event(model, buffer)
