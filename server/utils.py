import secrets
import string

from fastapi import WebSocket

from models.crud import get_room_by_id, get_db
from models.events import Event


def generate_room_id() -> str:
    """
    Helper function to generate a random room id.
    """
    usable = string.ascii_letters + string.digits
    id = ""
    for _ in range(6):
        id += secrets.choice(usable)

    db = get_db()

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


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    def add_room(self, room: str):
        if self.active_connections.get(room):
            raise Exception("this room already exists in the connections")

        self.active_connections[room] = []

    def delete_room(self, room: str):
        try:
            self.active_connections.pop(room)
        except KeyError:
            # its okay if keyerror pops up since the database and active_connections
            # dictionary could be inconsistent, especially when server restarts
            ...

    async def connect(self, room_id: str, websocket: WebSocket):
        conns = self.__find_all_conn_by_room(room_id)
        if conns is None:
            # dont have the condition as `not conns` because that also checks for zero length
            raise Exception(f"invalid {room_id=}")

        if len(conns) > 2:
            await websocket.close()
            return False

        await websocket.accept()
        self.active_connections[room_id].append(websocket)
        return True

    def __find_conn_by_websocket(self, websocket: WebSocket):
        for room in self.active_connections:
            if websocket in self.active_connections[room]:
                return (room, websocket)

        return None

    def __find_all_conn_by_room(self, room: str):
        return self.active_connections.get(room)

    async def disconnect(self, websocket: WebSocket):
        conn = self.__find_conn_by_websocket(websocket)
        if conn:
            room, _ = conn
            self.active_connections[room].remove(websocket)
            await websocket.close()

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_event(self, event: Event, websocket: WebSocket):
        await websocket.send_json(event.asdict())

    def is_room_ready(self, room: str):
        conns = self.__find_all_conn_by_room(room)
        if conns:
            return len(conns) == 2
        else:
            raise Exception(f"invalid room id {room}")

    async def broadcast_message(self, room: str, message: str):
        connections = self.__find_all_conn_by_room(room)
        if connections:
            print(f"sending '{message=}' to {connections=} in {room=}")
            for conn in connections:
                await conn.send_text(message)
        else:
            raise Exception(f"invalid room id {room}")

    async def broadcast_event(self, room: str, event: Event):
        connections = self.__find_all_conn_by_room(room)
        if connections:
            for conn in connections:
                await self.send_event(event, conn)
        else:
            raise Exception(f"invalid room id {room}")
