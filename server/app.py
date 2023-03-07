from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from models.rooms import CreateRoomResponse


app = FastAPI()


@app.get("/")
async def root():
    return HTMLResponse("The website is under development :)")


@app.post("/rooms/create")
async def create_room() -> CreateRoomResponse:
    pass