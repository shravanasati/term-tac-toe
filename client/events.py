from dataclasses import asdict, dataclass
from enum import StrEnum, auto
from typing import Any


class InvalidStructureException(Exception):
    """
    Raised when the `Event` class can't be constructed from a dictionary.
    """


class EventType(StrEnum):
    """
    Represents event types.
    """

    MESSAGE = auto()
    BOARD = auto()
    MOVE = auto()
    RESULT = auto()
    QUIT = auto()
    ASK_MOVE = auto()

    def __repr__(self) -> str:
        # overrides default enum repr
        return self.value


@dataclass(frozen=True, slots=True)
class Event:
    """
    Represents an event in the game. This is sent over to the client and back.
    """

    type_: EventType
    data: dict[str, Any]

    def asdict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, str | dict[str, Any]]):
        t = d.get("type_")
        d_ = d.get("data")
        if t is None or d is None or not isinstance(d_, dict):
            raise InvalidStructureException(
                f"missing fields to construct event class: {d}"
            )

        try:
            t_ = EventType(t)
        except ValueError:
            raise InvalidStructureException(f"event type {t} is unknown")

        return cls(t_, d_)


def message_event(message: str):
    """
    A helper function to create an `Event` with `EventType.MESSAGE`.
    """
    return Event(EventType.MESSAGE, {"message": message})


def board_event(board: list[list[int]]):
    """
    A helper function to create an `Event` with `EventType.BOARD`.
    """
    return Event(EventType.BOARD, {"board": [list(map(lambda x: x.value, row)) for row in board]})


if __name__ == "__main__":
    e = Event(EventType.BOARD, {"board": [1, 1, 3]})
    print(e)
    print(e.asdict())
