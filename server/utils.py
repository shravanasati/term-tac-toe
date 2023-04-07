import secrets
import string

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
        self.active_connections: list[tuple[str, WebSocket]] = []

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append((room_id, websocket))

    def __find_conn_by_websocket(self, websocket: WebSocket):
        for conn in self.active_connections:
            if conn[1] == websocket:
                return conn

    def __find_all_conn_by_room(self, room: str):
        websocket_list = []
        for conn in self.active_connections:
            if conn[0] == room:
                websocket_list.append(conn[1])

        return websocket_list

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(self.__find_conn_by_websocket(websocket))

    async def send_personal_message(self, message: str, websocket: WebSocket):
        conn = self.__find_conn_by_websocket(websocket)
        await conn[1].send_text(message)

    async def broadcast(self, room: str, message: str):
        connections = self.__find_all_conn_by_room(room)
        for conn in connections:
            await conn.send_text(message)
