from dataclasses import dataclass
import secrets
import string

from fastapi import WebSocket

from models.crud import db_session, get_room_by_id


def generate_room_id() -> str:
    """
    Helper function to generate a random room id.
    """
    usable = string.ascii_letters + string.digits
    id = ""
    for _ in range(6):
        id += secrets.choice(usable)

    with db_session() as db:
        while True:
            if get_room_by_id(id, db):
                id = ""
                for _ in range(6):
                    id += secrets.choice(usable)
            else:
                break

    return id


def generate_url_token() -> str:
    """
    Returns a random url safe token for `JoinRoomResponse`.
    """
    return secrets.token_urlsafe()


@dataclass
class Player:
    name: str
    ws: WebSocket
