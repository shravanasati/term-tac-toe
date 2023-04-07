import json
import logging
from threading import Thread
from time import sleep

import schedule
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from models import crud
from models.database import Base, engine
from models.requests import JoinRoomRequest
from models.responses import CreateRoomResponse, JoinRoomResponse

from utils import ConnectionManager, generate_room_id, generate_url_token, get_db

Base.metadata.create_all(bind=engine)
app = FastAPI()
conn_manager = ConnectionManager()

schedule.every().minute.do(crud.update_active_rooms, db=get_db())


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
        db = get_db()
        room_id = generate_room_id()
        crud.create_room(db, room_id)

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
        db = get_db()
        room = crud.get_room_by_id(db, room_request.room_id)

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
            db, room_request.room_id, room_request.player_name[:50], security_token
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


@app.websocket("/game/{room}")
async def gameplay(websocket: WebSocket, room: str, token: str):
    await conn_manager.connect(websocket)
    try:
        db = get_db()
        verified, player_name = crud.verify_player(db, room, token)
        if not verified:
            json_str = json.dumps({"message": "cannot verify the player"})
            await conn_manager.send_personal_message(json_str, websocket)

        await websocket.send_text("connection established")

        while True:
            data = await websocket.receive_text()
            await conn_manager.send_personal_message(f"You wrote: {data}", websocket)
            await conn_manager.broadcast(f"Client #{player_name} says: {data}")

    except WebSocketDisconnect:
        conn_manager.disconnect(websocket)
        await conn_manager.broadcast(f"Client #{player_name} left the game.")

    except Exception as e:
        print(e)
        json_str = json.dumps({"message": "An internal server error occured. Try again later."})
        await conn_manager.send_personal_message(json_str, websocket)
        await conn_manager.disconnect(websocket)

