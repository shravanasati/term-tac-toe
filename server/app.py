import asyncio
from contextlib import asynccontextmanager, suppress
from itertools import cycle
import json
import logging
import random
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import websockets

from models import crud
from models.database import init_db
from models.events import (
    EventType,
    ask_move_event,
    board_event,
    message_event,
    result_event,
)
from models.requests import JoinRoomRequest
from models.responses import CreateRoomResponse, JoinRoomResponse

from tic_tac_toe import LMPTicTacToe, Move
from utils import ConnectionManager, generate_room_id, generate_url_token

logging.basicConfig(level=logging.DEBUG)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    stop_event = asyncio.Event()

    async def room_cleaner_loop() -> None:
        while not stop_event.is_set():
            try:
                with crud.db_session() as db:
                    await crud.update_active_rooms(conn_manager=conn_manager, db=db)
            except Exception as e:
                logging.exception(e)

            try:
                await asyncio.wait_for(stop_event.wait(), timeout=60)
            except asyncio.TimeoutError:
                continue

    cleaner_task = asyncio.create_task(room_cleaner_loop())
    try:
        yield
    finally:
        stop_event.set()
        cleaner_task.cancel()
        with suppress(asyncio.CancelledError):
            await cleaner_task


app = FastAPI(lifespan=lifespan)
conn_manager = ConnectionManager()
room_game_tasks: dict[str, asyncio.Task[None]] = {}


async def room_game_loop(room_id: str) -> None:
    """Runs a single game loop per room.

    This avoids having both websocket endpoint coroutines attempting to
    `receive_json()` from the same websocket.
    """
    sent_waiting = False
    while True:
        players = conn_manager.active_connections.get(room_id)
        if players is None:
            return

        if len(players) == 2 and all(p.name for p in players):
            break

        if len(players) == 1 and not sent_waiting:
            sent_waiting = True
            await conn_manager.send_event(
                message_event("waiting for the other player to join..."),
                players[0].ws,
            )

        await asyncio.sleep(0.1)

    players = conn_manager.active_connections.get(room_id)
    if not players or len(players) != 2:
        return

    await conn_manager.broadcast_event(room_id, message_event("starting the game..."))

    starter_player = random.choice(players)
    other_player = players[0] if starter_player == players[1] else players[1]
    player_cycle = cycle([starter_player.name, other_player.name])
    game = LMPTicTacToe(starter_player.name, other_player.name, 3)
    await conn_manager.broadcast_event(room_id, board_event(game.board))

    while True:
        current_player_name = next(player_cycle)
        while True:
            current_player = conn_manager.find_player_by_name(
                room_id, current_player_name
            )
            if not current_player:
                await conn_manager.delete_room(room_id)
                return

            await conn_manager.send_event(
                ask_move_event(current_player_name),
                current_player.ws,
            )

            incoming = await conn_manager.receive_event(room_id, current_player.ws)
            if incoming is None:
                await conn_manager.broadcast_event(
                    room_id, message_event(f"{current_player_name} left the game.")
                )
                await conn_manager.delete_room(room_id)
                return

            match incoming.type_:
                case EventType.MOVE:
                    move = Move.from_dict(incoming.data["move"])
                    if move.marker != current_player_name:
                        await conn_manager.send_event(
                            message_event("youre not allowed to move yet"),
                            current_player.ws,
                        )
                        continue

                    game.fill_player_cell(move.marker, move.pos)
                    await conn_manager.broadcast_event(room_id, board_event(game.board))

                    over, result = game.game_outcome()
                    if over:
                        if result is None:
                            result_dict = {
                                "victory": False,
                                "winner": None,
                                "coordinates": None,
                            }
                            message = "It's a draw."
                        else:
                            result_dict = {
                                "victory": result.victory,
                                "winner": result.winner,
                                "coordinates": result.coordinates,
                            }
                            message = f"{result.winner} wins the game."

                        await conn_manager.broadcast_event(
                            room_id,
                            result_event(game.board, result_dict, message),
                        )
                        await conn_manager.delete_room(room_id)
                        return

                    break

                case EventType.QUIT:
                    await conn_manager.disconnect(room_id, current_player.ws)
                    await conn_manager.broadcast_event(
                        room_id, message_event(f"{current_player_name} left the game.")
                    )
                    await conn_manager.delete_room(room_id)
                    return

                case _:
                    await conn_manager.send_event(
                        message_event(f"unknown {incoming=} recieved"),
                        current_player.ws,
                    )
                    continue


@app.get("/")
def root():
    return HTMLResponse("<h1> The website is under development :) </h1>")


@app.post("/rooms/create")
def create_room() -> CreateRoomResponse:
    try:
        with crud.db_session() as db:
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
        with crud.db_session() as db:
            room = crud.get_room_by_id(room_request.room_id, db)

            if not room:
                failure_response.message = (
                    f"Room with room id `{room_request.room_id}` doesn't exist."
                )
                return failure_response

            if not room.is_active:
                failure_response.message = "This room is no longer active. Create a new room to continue playing."
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
    player_name: str = "unknown"
    try:
        connected = await conn_manager.connect(room_id, websocket)
        if not connected:
            # room must be full
            return

        with crud.db_session() as db:
            room = crud.get_room_by_id(room_id, db)
        if not room:
            logging.debug("room not found in gameplay endpoint")
            await conn_manager.disconnect(room_id, websocket)
            return

        with crud.db_session() as db:
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

        reader_task = asyncio.create_task(conn_manager.read_events(room_id, websocket))
        try:
            if room_id not in room_game_tasks:
                task = asyncio.create_task(room_game_loop(room_id))

                def _cleanup(_: asyncio.Task) -> None:
                    room_game_tasks.pop(room_id, None)

                task.add_done_callback(_cleanup)
                room_game_tasks[room_id] = task

            await room_game_tasks[room_id]
        finally:
            reader_task.cancel()
            with suppress(asyncio.CancelledError):
                await reader_task

    except (
        WebSocketDisconnect,
        websockets.exceptions.ConnectionClosed,
        asyncio.CancelledError,
    ):
        # todo handle disconnects
        if isinstance(websocket, WebSocket):
            await conn_manager.disconnect(room_id, websocket)
            await conn_manager.broadcast_event(
                room_id, message_event(f"Client #{player_name} left the game.")
            )

    except Exception as e:
        logging.exception(e)
        print(e)
        error_event = message_event(
            "An internal server error occured. Try again later."
        )
        await conn_manager.send_event(error_event, websocket)
        await conn_manager.disconnect(room_id, websocket)
