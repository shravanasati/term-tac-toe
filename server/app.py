import asyncio
from contextlib import asynccontextmanager
from itertools import cycle
import json
import logging
import random
from threading import Thread
from time import sleep

import schedule
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import websockets

from models import crud
from models.database import init_db
from models.events import Event, EventType, ask_move_event, board_event, message_event
from models.requests import JoinRoomRequest
from models.responses import CreateRoomResponse, JoinRoomResponse

from tic_tac_toe import LMPTicTacToe, Move
from utils import ConnectionManager, generate_room_id, generate_url_token, get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)
conn_manager = ConnectionManager()

schedule.every().minute.do(
    crud.update_active_rooms, db=get_db(), conn_manager=conn_manager
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
        db = get_db()
        room_id = generate_room_id()
        crud.create_room(room_id, db)
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
        db = get_db()
        room = crud.get_room_by_id(room_request.room_id, db)

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
            room_request.room_id,
            room_request.player_name[:50],
            security_token,
            db,
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

        db = get_db()
        room = crud.get_room_by_id(room_id, db)
        if not room:
            logging.debug("room not found in gameplay endpoint")
            return

        verified, player_name = crud.verify_player(room_id, token, db)
        if not verified:
            json_str = json.dumps({"message": "cannot verify the player"})
            await conn_manager.send_personal_message(json_str, websocket)
            await conn_manager.disconnect(room_id, websocket)
            return

        conn_manager.add_player_name(room_id, player_name, websocket)

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

        # difficulty doesnt matter here
        starter_player = random.choice([room.player1, room.player2])
        other_player = room.player1 if starter_player == room.player2 else room.player2
        player_cycle = cycle([starter_player, other_player])
        game = LMPTicTacToe(starter_player, other_player, 3)
        await conn_manager.broadcast_event(room_id, board_event(game.board))

        while True:
            # todo maintain the game state, player cycle in connection
            current_player_name = next(player_cycle)
            current_player = conn_manager.find_player_by_name(
                room_id, current_player_name
            )
            if not current_player:
                raise Exception("unable to find current player!")

            await conn_manager.send_event(
                ask_move_event(current_player_name), current_player.ws
            )

            data = await websocket.receive_json()
            event = Event.from_dict(data)
            match event.type_:
                case EventType.MOVE:
                    move = Move.from_dict(event.data["move"])
                    if move.marker != current_player_name:
                        await conn_manager.send_event(
                            message_event("youre not allowed to move yet"), websocket
                        )

                    else:
                        game.fill_player_cell(move.marker, move.pos)
                        await conn_manager.broadcast_event(
                            room_id, board_event(game.board)
                        )

                case EventType.QUIT:
                    # todo make the other player win
                    await conn_manager.disconnect(room_id, websocket)
                    await conn_manager.broadcast_event(
                        room_id, message_event(f"{player_name} left the game.")
                    )
                    await conn_manager.broadcast_message(
                        room_id, f"{player_name} left the game."
                    )
                    await conn_manager.delete_room(room_id)
                case _:
                    await conn_manager.send_event(
                        message_event(f"unknown {event=} recieved"), websocket
                    )

    except (WebSocketDisconnect, websockets.exceptions.ConnectionClosed):
        # todo handle disconnects
        await conn_manager.disconnect(room_id, websocket)
        await conn_manager.broadcast_message(
            room_id, f"Client #{player_name} left the game."
        )

    except Exception as e:
        logging.exception(e)
        print(e)
        error_event = message_event(
            "An internal server error occured. Try again later."
        )
        await conn_manager.send_event(error_event, websocket)
        await conn_manager.disconnect(room_id, websocket)
