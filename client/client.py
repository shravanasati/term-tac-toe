import asyncio
import json
import re
import requests
from rich.prompt import Prompt
import websockets

from tic_tac_toe import Difficulty, TicTacToe, Cell, CheckWinResult, Move
from events import Event, EventType

base_server_url = "http://127.0.0.1:8000"
base_server_ws = "ws://127.0.0.1:8000"

# todo add validation for player name, must not be greater than 50 chars
# todo commas and symbols not allowed in player name


def create_room():
    resp = requests.post(f"{base_server_url}/rooms/create")

    if resp.status_code != 200:
        print("Unable to request the server!")
        quit(1)
    
    resp = resp.json()
    if not resp["success"]:
        print("Cannot create a room.")
        print(resp["message"])
        quit()

    return resp["room_id"]


async def main():
    prompt_text = "What do you want to do? \n1. Create a room \n2. Join a room\n"
    choice = Prompt.ask(prompt_text, choices=["1", "2"])

    if choice == "1":
        room_id = create_room()
        print(f"Room with room id `{room_id}` created successfully.")
    else:
        room_id_regex = re.compile(r"[\dA-Za-z]{6}")
        while True:
            room_id = Prompt.ask("Enter the six-digit room id")
            if not room_id_regex.match(room_id):
                print("Invalid room id, try again.")
                continue

            break

    player_name = Prompt.ask("Enter a nickname")
    payload = {"room_id": room_id, "player_name": player_name}
    join_resp = requests.post(
        f"{base_server_url}/rooms/join", json=payload
    ).json()

    # print(join_resp)
    if not join_resp["success"]:
        print("Unable to join the room.")
        print(join_resp["message"])
        quit(1)

    redirect = join_resp["websocket_redirect"]
    token = join_resp["token"]
    websocket_url = f"{base_server_ws}{redirect}?token={token}"

    async with websockets.connect(websocket_url) as ws:
        try:
            game = TicTacToe(Difficulty.EASY, 3)
            while True:
                data = json.loads(await ws.recv())
                event = Event.from_dict(data)
                match event.type_:
                    case EventType.BOARD:
                        game.board = [
                            list(map(lambda x: Cell(x), row))
                            for row in event.data["board"]
                        ]
                        game.display_board()

                    case EventType.ASK_MOVE:
                        if event.data["player"] != player_name:
                            continue
                        pos = game.position_input()
                        move = Move(pos, player_name)
                        move_event = Event(EventType.MOVE, {"move": move.asdict()})
                        await ws.send(json.dumps(move_event.asdict()))

                    case EventType.RESULT:
                        game.board = game.board = [
                            list(map(lambda x: Cell(x), row))
                            for row in event.data["board"]
                        ]
                        game.display_board(CheckWinResult.from_dict(event.data["result"]))
                        print(event.data["message"])
                        return

                    case EventType.MESSAGE:
                        print(f"server> {event.data['message']}")

                    case _:
                        raise Exception(f"unknown {event=} recieved from server")

        except KeyboardInterrupt:
            quit(1)


if __name__ == "__main__":
    asyncio.run(main())
