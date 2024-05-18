import asyncio
from contextlib import asynccontextmanager
import json
import logging
from threading import Thread
from time import sleep

import schedule
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import websockets

from models import crud
from models.database import init_db, db_session
from models.events import Event, EventType, message_event
from models.requests import JoinRoomRequest
from models.responses import CreateRoomResponse, JoinRoomResponse

from utils import ConnectionManager, generate_room_id, generate_url_token


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    db_session.remove()


app = FastAPI(lifespan=lifespan)
conn_manager = ConnectionManager()

schedule.every().minute.do(
    crud.update_active_rooms, db_session, conn_manager=conn_manager
)


def cleaning_job():
    while True:
        schedule.run_pending()
        sleep(1)


t = Thread(target=cleaning_job)
t.start()


@app.get("/")
def root():
    return HTMLResponse("<h1> The website is under development :) </h1>")


@app.post("/rooms/create")
def create_room() -> CreateRoomResponse:
    try:
        room_id = generate_room_id()
        crud.create_room(db_session, room_id)
        conn_manager.add_room(room_id)

        return CreateRoomResponse(
            success=True, message="Room created successfully.", room_id=room_id
        )

    except Exception as e:
        logging.exception(e)
        return CreateRoomResponse(
            success=False,
            message="There was an internal error in the server.",
            room_id="",
        )


@app.post("/rooms/join")
def join_room(room_request: JoinRoomRequest) -> JoinRoomResponse:
    try:
        failure_response = JoinRoomResponse(
            success=False, message="", websocket_redirect="", token=""
        )
        room = crud.get_room_by_id(db_session, room_request.room_id)

        if not room:
            failure_response.message = (
                f"Room with room id `{room_request.room_id}` doesn't exist."
            )
            return failure_response

        if not room.is_active:
            failure_response.message = (
                "This room is no longer active. Create a new room to continue playing."
            )
            return failure_response

        security_token = generate_url_token()
        ok, message = crud.add_player_to_room(
            db_session,
            room_request.room_id,
            room_request.player_name[:50],
            security_token,
        )

        if ok:
            return JoinRoomResponse(
                success=True,
                message=f"Successfully added player `{room_request.player_name}` to room with id `{room_request.room_id}`.",
                websocket_redirect=f"/game/{room_request.room_id}",
                token=security_token,
            )

        else:
            failure_response.message = message
            return failure_response

    except Exception as e:
        logging.exception(e)
        failure_response.message = (
            "An internal error occured in the server. Try again later."
        )
        return failure_response


@app.websocket("/game/{room_id}")
async def gameplay(websocket: WebSocket, room_id: str, token: str):
    try:
        connected = await conn_manager.connect(room_id, websocket)
        if not connected:
            # room must be full
            return

        verified, player_name = crud.verify_player(db_session, room_id, token)
        if not verified:
            json_str = json.dumps({"message": "cannot verify the player"})
            await conn_manager.send_personal_message(json_str, websocket)
            await conn_manager.disconnect(websocket)
            return

        await conn_manager.send_event(
            message_event("connection established"), websocket
        )

        playable = conn_manager.is_room_ready(room_id)

        if not playable:
            await conn_manager.send_event(
                message_event("waiting for the other player to join..."), websocket
            )

        while not playable:
            playable = conn_manager.is_room_ready(room_id)
            await asyncio.sleep(0.1)

        await conn_manager.send_event(message_event("starting the game..."), websocket)

        while True:
            data = await websocket.receive_json()
            event = Event.from_dict(data)
            match event.type_:
                case EventType.QUIT:
                    await conn_manager.disconnect(websocket)
                    await conn_manager.broadcast_event(
                        room_id, message_event(f"{player_name} left the game.")
                    )
                    await conn_manager.broadcast_message(
                        room_id, f"{player_name} left the game."
                    )
                case _:
                    await conn_manager.send_event(
                        message_event(f"unknown {event=} recieved"), websocket
                    )

            await conn_manager.send_personal_message(f"You wrote: {data}", websocket)
            await conn_manager.broadcast_message(
                room_id, f"Client #{player_name} says: {data}"
            )

    except (WebSocketDisconnect, websockets.exceptions.ConnectionClosed):
        # todo handle disconnects
        await conn_manager.disconnect(websocket)
        await conn_manager.broadcast_message(
            room_id, f"Client #{player_name} left the game."
        )

    except Exception as e:
        logging.exception(e)
        json_str = json.dumps(
            {"message": "An internal server error occured. Try again later."}
        )
        await conn_manager.send_personal_message(json_str, websocket)
        await conn_manager.disconnect(websocket)
