from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import now

from .dbmodels import Room
# todo add players to database from join function


def get_room_by_id(db: Session, room_id: str):
    return db.query(Room).filter(Room.room_id == room_id).first()


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
