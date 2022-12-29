from __future__ import annotations

from asyncio.subprocess import Process
from dataclasses import dataclass
from enum import Enum
from json import dumps
from struct import unpack
from typing import Optional, Union


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


def decode_screen_event(buffer: bytes) -> ScreenInputEvent:
    """Decode the bytes received from the screen events.

    Some part of the buffer are not decoded:
        buffer[4:8]

    See:
        https://github.com/ichaozi/RemarkableFramebuffer
        https://github.com/canselcik/libremarkable
    """
    return ScreenInputEvent(
        timestamp=unpack("f", buffer[0:4])[0],
        type=EventTypes(unpack("h", buffer[8:10])[0]),
        code=EventCodes(unpack("h", buffer[10:12])[0]),
        value=unpack("i", buffer[12:16])[0],
    )


async def get_screen_input(subprocess_shell: Process) -> Optional[ScreenInputEvent]:
    buffer: bytes = await subprocess_shell.stdout.read(16)

    if not len(buffer) == 16:
        raise ValueError(f"Buffer is not 16 bits: {len(buffer)=} {buffer=}")

    return decode_screen_event(buffer)
