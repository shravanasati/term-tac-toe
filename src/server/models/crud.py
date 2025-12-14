from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

from sqlalchemy.orm import Session

from .database import SessionLocal
from .dbmodels import GameStatus, Room


def get_db():
    return SessionLocal()


@contextmanager
def db_session() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_room_by_id(room_id: str, db: Session) -> Room | None:
    return (db).query(Room).filter_by(room_id=room_id).first()


def add_player_to_room(
    room_id: str, player_name: str, token: str, db: Session
) -> tuple[bool, str]:
    """
    Adds `player_name` to the room with given `room_id`.

    Returns boolean value of whether player was added to the room (by checking room capacity.)
    """
    room: Room = db.query(Room).filter(Room.room_id == room_id).first()

    if "," in player_name:
        return (
            False,
            "Invalid name. Player name can't contain any symbols. Only letters and numbers are allowed.",
        )

    if room.player1 == "":
        if player_name == room.player2:
            return (
                False,
                "A player with the same name already exists in the room. Try again with a different name.",
            )

        room.player1 = player_name
        room.token1 = token
        room.is_active = True
        db.commit()
        return True, ""

    elif room.player2 == "":
        if player_name == room.player1:
            return (
                False,
                "A player with the same name already exists in the room. Try again with a different name.",
            )

        room.player2 = player_name
        room.token2 = token

        # Both players joined, start the game
        if room.player1 and room.player2:
            room.game_status = GameStatus.PLAYING
            room.current_turn = room.player1
            room.board_state = "---------"
            room.winner = ""

        db.commit()
        return True, ""

    else:
        return False, "This room is already full."


def verify_player(room_id: str, token: str, db: Session) -> tuple[bool, str]:
    room = get_room_by_id(room_id, db)
    if not room:
        print("no room found")
        return False, ""
    if room.token1 == token:
        return True, room.player1
    elif room.token2 == token:
        return True, room.player2
    else:
        return False, ""


def get_active_rooms(db: Session):
    return db.query(Room).filter(Room.is_active)


def create_room(room_id: str, db: Session):
    room = Room(room_id=room_id)
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


async def update_active_rooms(conn_manager, db: Session):
    print("updating active rooms")
    active_rooms = get_active_rooms(db)

    for room in active_rooms:
        if room.created_on is None:
            continue

        # Guard: never drop rooms that currently have connected players.
        # (Active games / waiting rooms should not be cleaned up.)
        room_id = str(room.room_id)
        active_conns = getattr(conn_manager, "active_connections", {}).get(room_id)
        if active_conns is not None and len(active_conns) > 0:
            continue

        age_seconds = (datetime.utcnow() - room.created_on).total_seconds()
        if age_seconds > 60 * 60 * 2:
            db.delete(room)
            await conn_manager.delete_room(room_id)

    db.commit()


def update_room_game_state(
    room_id: str,
    board_state: str,
    current_turn: str,
    game_status: GameStatus,
    winner: str,
    db: Session,
):
    room = get_room_by_id(room_id, db)
    if room:
        room.board_state = board_state
        room.current_turn = current_turn
        room.game_status = game_status
        room.winner = winner
        db.commit()


def get_room_with_players(room_id: str, db: Session) -> Room | None:
    return db.query(Room).filter(Room.room_id == room_id).first()


def reset_game_after_rematch(room_id: str, db: Session):
    room = get_room_by_id(room_id, db)
    if room:
        room.board_state = "---------"
        room.winner = ""
        room.game_status = GameStatus.PLAYING
        room.current_turn = room.player1  # Player 1 always starts
        db.commit()


def get_rematch_votes(room_id: str, db: Session) -> dict[str, bool]:
    room = get_room_by_id(room_id, db)
    if not room:
        return {}

    # This would be stored in the database in a real implementation
    # For now, we'll track this in memory in the connection manager
    return {}
