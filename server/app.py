import logging
from threading import Thread
from time import sleep

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import schedule

from models import crud
from models.database import Base, engine
from models.responses import CreateRoomResponse, JoinRoomResponse
from models.requests import JoinRoomRequest

from utils import generate_room_id, get_db, ConnectionManager


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
async def root():
    return HTMLResponse("The website is under development :)")


@app.post("/rooms/create")
async def create_room() -> CreateRoomResponse:
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
async def join_room(room_request: JoinRoomRequest) -> JoinRoomResponse:
    try:
        db = get_db()
        room = crud.get_room_by_id(db, room_request.room_id)

        if not room:
            return JoinRoomResponse(
                success=False,
                message=f"Room with room id `{room_request.room_id}` doesn't exist.",
                websocket_redirect="",
            )

        ok = crud.add_player_to_room(
            db, room_request.room_id, room_request.player_name[:50]
        )

        if ok:
            # todo return websocket url
            return JoinRoomResponse(
                success=True,
                message=f"Successfully added player `{room_request.player_name}` to room with id `{room_request.room_id}`.",
                websocket_redirect=""
            )

        else:
            return JoinRoomResponse(
                success=False,
                message="Room is already full.",
                websocket_redirect="",
            )

    except Exception as e:
        logging.exception(e)
        return JoinRoomResponse(
            success=False,
            message="An internal server error occured.",
            websocket_redirect="",
        )
