from __future__ import annotations

from asyncio.subprocess import Process
from dataclasses import dataclass
from enum import Enum, IntEnum
from json import dumps
from struct import unpack
from typing import Optional, Union


class DeviceTypes(IntEnum):
    """The ReMarkable has two inputs method outputting on two differents /dev/input
    for the touch screen gestures and for the stylus."""
    PEN = 0
    TOUCH = 1


class EventTypes(IntEnum):
    """Type of events."""
    SYNC = 0
    KEY = 1  # Represents the interaction tool (?) like the pen used
    RELATIVE = 2
    ABSOLUTE = 3  # Represents data on the screen in absolute value


class PenEventCodes(IntEnum):
    """For the stylus, which data point the value is a reference of, by evdev driver codes.
    
    Returns cls.UNKNOWN for missing values.
    Mixes codes from EventTypes.ABSOLUTE and EventTypes.KEY (and probably also the others in UNKNOWN).

    The value is the direct int representation of the buffer.
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
    UNKNOWN = -1

    @classmethod
    def _missing_(cls, value: str) -> PenEventCodes:
        """Provides a fallback value for unrepresented values to cls.UNKNOWN"""
        print(f"{cls} can not represent {value}. Defaulting to {cls.UNKNOWN}")
        return cls.UNKNOWN


class TouchEventCodes(IntEnum):
    """For the touch gestures, which data point the value is a reference of, by evdev driver codes.

    
    Returns cls.UNKNOWN for missing values.
    The value is the direct int representation of the buffer.
    """
    DISCARD = 0
    SLOT = 47  # if present, more than one finger on the screen, each value represents a finger
    X = 53
    Y = 54
    PRESSURE = 58
    IGNORE = 65535
    TRACKING_ID = 57 # send when starting to touch the screen with a value, send when releasing with value -1
    TOUCH_MAJOR = 48
    TOUCH_MINOR = 49
    ORIENTATION = 52
    TOOL_TYPE = 55
    DISTANCE = 25
    UNKNOWN = -1

    @classmethod
    def _missing_(cls, value: str) -> TouchEventCodes:
        """Provides a fallback value for unrepresented values to cls.UNKNOWN"""
        print(f"{cls} can not represent {value}. Defaulting to {cls.UNKNOWN}")
        return cls.UNKNOWN


@dataclass
class ScreenInputEvent:
    """Represent the data contained in a screen event payload."""
    timestamp: float
    type: EventTypes
    code: PenEventCodes
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


def decode_screen_event(buffer: bytes, device_type: DeviceTypes) -> ScreenInputEvent:
    """Decode the bytes received from the screen events.

    Some part of the buffer are not decoded:
        buffer[4:8]

    For more information:
        Basic inputs of the remarkable models: https://remarkablewiki.com/devel/handling_input
        evdev driver codes: https://docs.rs/evdev/0.10.1/evdev/struct.AbsoluteAxis.html
        Explantion of the protocol: https://www.kernel.org/doc/Documentation/input/multi-touch-protocol.txt
    """
    return ScreenInputEvent(
        timestamp=unpack("f", buffer[0:4])[0],
        type=EventTypes(unpack("h", buffer[8:10])[0]),
        code=(
            PenEventCodes(unpack("h", buffer[10:12])[0])
            if device_type == DeviceTypes.PEN
            else TouchEventCodes(unpack("h", buffer[10:12])[0])
        ),
        value=unpack("i", buffer[12:16])[0],
    )


async def get_screen_input(subprocess_shell: Process, device_type: DeviceTypes = DeviceTypes.PEN) -> Optional[ScreenInputEvent]:
    buffer: bytes = await subprocess_shell.stdout.read(16)

    if not len(buffer) == 16:
        raise ValueError(f"Buffer is not 16 bits: {len(buffer)=} {buffer=}")

    return decode_screen_event(buffer, device_type)
