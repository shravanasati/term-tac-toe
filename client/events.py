from dataclasses import asdict, dataclass
from enum import StrEnum, auto
from typing import Any
from tic_tac_toe import Cell


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
    ROOM_STATUS = auto()
    REMATCH_VOTE = auto()

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


def board_event(board: list[list[Cell]]):
    """
    A helper function to create an `Event` with `EventType.BOARD`.
    """
    return Event(
        EventType.BOARD, {"board": [list(map(lambda x: x.value, row)) for row in board]}
    )


def ask_move_event(player_name: str):
    """
    A helper function to create an `Event` with `EventType.ASK_MOVE`.
    """
    return Event(EventType.ASK_MOVE, {"player": player_name})


def room_status_event(status: str, players: list[str], current_turn: str, winner: str):
    """
    A helper function to create an `Event` with `EventType.ROOM_STATUS`.
    """
    return Event(EventType.ROOM_STATUS, {
        "status": status,
        "players": players,
        "current_turn": current_turn,
        "winner": winner
    })


def rematch_vote_event(votes: dict[str, bool], all_voted: bool):
    """
    A helper function to create an `Event` with `EventType.REMATCH_VOTE`.
    """
    return Event(EventType.REMATCH_VOTE, {"votes": votes, "all_voted": all_voted})


def result_event(board: list[list[Cell]], result: dict[str, Any], message: str):
    """Create an `Event` with `EventType.RESULT`.

    The client expects:
    - data.board: 2D list of ints (Cell enum values)
    - data.result: dict compatible with `CheckWinResult.from_dict`
    - data.message: user-facing string
    """
    return Event(
        EventType.RESULT,
        {
            "board": [list(map(lambda x: x.value, row)) for row in board],
            "result": result,
            "message": message,
        },
    )


if __name__ == "__main__":
    e = Event(EventType.BOARD, {"board": [1, 1, 3]})
    print(e)
    print(e.asdict())
