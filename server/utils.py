from dataclasses import dataclass
import secrets
import string
import asyncio

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from models.crud import db_session, get_room_by_id
from models.events import Event


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


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[Player]] = {}
        # Per-room, per-websocket incoming event queues.
        # Keyed by id(websocket) to avoid relying on WebSocket hashing semantics.
        self._incoming_events: dict[str, dict[int, asyncio.Queue[Event | None]]] = {}

    def add_room(self, room: str):
        if self.active_connections.get(room):
            raise Exception("this room already exists in the connections")

        self.active_connections[room] = []
        self._incoming_events.setdefault(room, {})

    def add_player_name(self, room_id: str, player_name: str, ws: WebSocket):
        for player in self.active_connections[room_id]:
            if player.ws == ws:
                player.name = player_name
                return

        self.active_connections[room_id].append(Player(player_name, ws))

    async def delete_room(self, room: str):
        players = self.active_connections.get(room)
        if players is None:
            return

        for player in list(players):
            try:
                await player.ws.close()
            except RuntimeError:
                pass
            except Exception:
                pass

        self.active_connections.pop(room, None)
        self._incoming_events.pop(room, None)

    async def connect(self, room_id: str, websocket: WebSocket):
        conns = self.__find_all_conn_by_room(room_id)
        if conns is None:
            # dont have the condition as `not conns` because that also checks for zero length
            # This can happen after a server restart: DB has the room but memory doesn't.
            with db_session() as db:
                room = get_room_by_id(room_id, db)
            if room and getattr(room, "is_active", True):
                self.active_connections[room_id] = []
                self._incoming_events.setdefault(room_id, {})
                conns = self.active_connections[room_id]
            else:
                raise Exception(f"invalid {room_id=}")

        if len(conns) >= 2:
            await websocket.close()
            return False

        await websocket.accept()
        self.active_connections[room_id].append(Player("", websocket))
        self._incoming_events.setdefault(room_id, {})[id(websocket)] = asyncio.Queue()
        return True

    def find_player_by_name(self, room_id: str, player_name: str):
        for player in self.active_connections[room_id]:
            if player.name == player_name:
                return player

    def __find_player_by_websocket(self, room_id: str, websocket: WebSocket):
        for player in self.active_connections.get(room_id, []):
            if websocket == player.ws:
                return player

    def __find_all_conn_by_room(self, room: str):
        return self.active_connections.get(room)

    async def disconnect(self, room_id: str, websocket: WebSocket):
        player = self.__find_player_by_websocket(room_id, websocket)
        if player:
            self.active_connections[room_id].remove(player)
            self._incoming_events.get(room_id, {}).pop(id(websocket), None)
            try:
                if (
                    websocket.application_state == WebSocketState.CONNECTED
                    or websocket.client_state == WebSocketState.CONNECTED
                ):
                    await websocket.close()
            except RuntimeError:
                # Socket already closed / close frame already sent.
                return

    async def read_events(self, room_id: str, websocket: WebSocket):
        """Continuously read incoming websocket messages into a per-socket queue.

        Exactly one task should call this per websocket.
        """
        queue = self._incoming_events.get(room_id, {}).get(id(websocket))
        if queue is None:
            return

        try:
            while True:
                data = await websocket.receive_json()
                event = Event.from_dict(data)
                await queue.put(event)
        except Exception:
            # Any receive error means the connection is gone.
            try:
                await queue.put(None)
            except Exception:
                return

    async def receive_event(self, room_id: str, websocket: WebSocket) -> Event | None:
        queue = self._incoming_events.get(room_id, {}).get(id(websocket))
        if queue is None:
            return None
        return await queue.get()

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def send_event(self, event: Event, websocket: WebSocket):
        # Starlette raises RuntimeError if you try to send after a close.
        # This can legitimately happen during disconnect races.
        try:
            if (
                websocket.application_state != WebSocketState.CONNECTED
                or websocket.client_state != WebSocketState.CONNECTED
            ):
                return
            await websocket.send_json(event.asdict())
        except RuntimeError:
            return

    def is_room_ready(self, room: str):
        conns = self.__find_all_conn_by_room(room)
        if conns is None:
            raise Exception(f"invalid room id {room}")
        return len(conns) == 2

    async def broadcast_message(self, room: str, message: str):
        connections = self.__find_all_conn_by_room(room)
        if connections is None:
            return
        print(f"sending '{message=}' to {connections=} in {room=}")
        for conn in connections:
            await conn.ws.send_text(message)

    async def broadcast_event(self, room: str, event: Event):
        connections = self.__find_all_conn_by_room(room)
        if connections is None:
            return
        for conn in connections:
            await self.send_event(event, conn.ws)
