"""Decode and simplify into actions the pressure points (fingers) events on the screen.

For the time being, it only supports one finger.
"""

from dataclasses import dataclass, field
from  typing import Optional, TypedDict
from src.screen_api import DeviceTypes, EventTypes, TouchEventCodes, get_screen_input


@dataclass
class Slot:
    """Represents a pressure point (a finger)"""
    id: int
    y: float = field(init=False, default=None)
    x: float = field(init=False, default=None)
    pressure: float = field(init=False, default=None)


@dataclass
class Payload:
    """Represents all the pressures point at a given moment."""
    slots: dict[int, Slot] = field(init=False, default_factory=dict)


async def get_screen_gestures(listener) -> Payload:
    """Group into a consistent dataclass the stream of touch screen inputs"""
    payload = Payload()
    current_slot: Optional[Slot] = None

    while True:
        screen_input = await get_screen_input(listener, DeviceTypes.TOUCH)

        if not screen_input:
            continue
        # It's sending coordinates
        if screen_input.type == EventTypes.ABSOLUTE:
            # Slot event is not sent when there is only one pressure point
            if screen_input.code == TouchEventCodes.SLOT or current_slot is None:
                slot_id = screen_input.value or -1
                payload.slots[slot_id] = Slot(id=slot_id)
                current_slot = payload.slots[slot_id]
            elif screen_input.code == TouchEventCodes.X:
                print(f"X {screen_input.value=}")
                current_slot.x = screen_input.value
            elif screen_input.code == TouchEventCodes.Y:
                current_slot.y = screen_input.value
            elif screen_input.code == TouchEventCodes.PRESSURE:
                current_slot.pressure = screen_input.value
            else:
                print(f"Touch: {screen_input=}")
        elif screen_input.type == EventTypes.SYNC:
            return payload
