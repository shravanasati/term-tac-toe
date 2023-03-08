from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import now

from .dbmodels import Room


def get_room_by_id(db: Session, room_id: str) -> Room | None:
    return db.query(Room).filter(Room.room_id == room_id).first()


def add_player_to_room(db: Session, room_id: str, player_name: str) -> bool:
    """
    Adds `player_name` to the room with given `room_id`.

    Returns boolean value of whether player was added to the room (by checking room capacity.)
    """
    room: Room = db.query(Room).filter(Room.room_id == room_id).first()

    if "," in player_name:
        return False

    if room.player1 == "":
        room.player1 = player_name
        db.commit()
        return True

    elif room.player2 == "":
        room.player2 = player_name
        db.commit()
        return True

    else:
        return False


def get_active_rooms(db: Session):
    return db.query(Room).filter(Room.is_active)


def create_room(db: Session, room_id: str):
    room = Room(room_id=room_id)
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


def update_active_rooms(db: Session):
    active_rooms = get_active_rooms(db).filter(now - Room.created_on > 1)
    for room in active_rooms:
        db.delete(room)

    db.flush()
