from datetime import datetime

from sqlalchemy.orm import Session

from .dbmodels import Room


def get_room_by_id(db: Session, room_id: str) -> Room | None:
    return db.query(Room).filter(Room.room_id == room_id).first()


def add_player_to_room(
    db: Session, room_id: str, player_name: str, token: str
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
        db.commit()
        return True, ""

    else:
        return False, "This room is already full."


def get_active_rooms(db: Session):
    return db.query(Room).filter(Room.is_active)


def create_room(db: Session, room_id: str):
    room = Room(room_id=room_id)
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


def update_active_rooms(db: Session):
    # print("updating active rooms")
    active_rooms = get_active_rooms(db).filter(Room.is_active)

    for room in active_rooms:
        hour_diff = datetime.now() - room.created_on
        if hour_diff.seconds > 60 * 60:
            db.delete(room)

    db.commit()
