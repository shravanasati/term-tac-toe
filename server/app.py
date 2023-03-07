import logging
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from models import crud
from models.database import Base, engine
from models.responses import CreateRoomResponse

from utils import generate_room_id, get_db


Base.metadata.create_all(bind=engine)
app = FastAPI()


@app.get("/")
async def root():
    return HTMLResponse("The website is under development :)")


@app.post("/rooms/create")
async def create_room() -> CreateRoomResponse:
    try:
        db = get_db()
        room_id = generate_room_id()
        crud.create_room(db, room_id)

        return CreateRoomResponse(success=True, message="Room created successfully.", room_id=room_id)

    except Exception as e:
        logging.exception(e)
        return CreateRoomResponse(success=False, message="There was an internal error in the server.", room_id="")
