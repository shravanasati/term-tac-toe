import string
import secrets

from fastapi import WebSocket

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
        id += secrets.choice(usable)

    while True:
        if get_room_by_id(get_db(), id):
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


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)
