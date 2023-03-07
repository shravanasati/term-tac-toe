import random
import string

from models.crud import get_room_by_id
from models.database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()


def generate_room_id() -> str:
    """
    Helper function to generate a random room id.
    """
    usable = string.ascii_letters + string.digits
    id = ""
    for _ in range(6):
        id += usable[random.randint(0, len(usable))]

    while True:
        if get_room_by_id(get_db(), id):
            id = ""
            for _ in range(6):
                id += usable[random.randint(0, len(usable))]
        else:
            break

    return id
