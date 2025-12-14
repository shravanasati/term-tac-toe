import argparse
import asyncio
import json
import re
import requests
from rich.prompt import Prompt
from rich.console import Console
from rich.panel import Panel
import websockets

from tic_tac_toe import Difficulty, TicTacToe, Cell, CheckWinResult, Move
from events import Event, EventType

DEFAULT_SERVER_IP = "104.248.22.239"

console = Console()

# todo add validation for player name, must not be greater than 50 chars
# todo commas and symbols not allowed in player name


def create_room(base_server_url):
    console.print("[bold green]Creating a new room...[/bold green]")
    resp = requests.post(f"{base_server_url}/rooms/create")

    if resp.status_code != 200:
        console.print("[bold red]Unable to request the server![/bold red]")
        quit(1)

    resp = resp.json()
    if not resp["success"]:
        console.print("[bold red]Cannot create a room.[/bold red]")
        console.print(resp["message"])
        quit()

    console.print(
        f"[bold green]Room created successfully with ID: {resp['room_id']}[/bold green]"
    )
    return resp["room_id"]


async def main(server_ip):
    base_server_url = f"http://{server_ip}"
    base_server_ws = f"ws://{server_ip}"
    console.print(
        Panel.fit("[bold]Welcome to Tic-Tac-Toe![/bold]", border_style="blue")
    )
    prompt_text = "What do you want to do? \n1. Create a room \n2. Join a room\n"
    choice = Prompt.ask(prompt_text, choices=["1", "2"])

    if choice == "1":
        room_id = create_room(base_server_url)
    else:
        room_id_regex = re.compile(r"[\dA-Za-z]{6}")
        while True:
            room_id = Prompt.ask("[bold]Enter the six-digit room id[/bold]")
            if not room_id_regex.match(room_id):
                console.print("[bold red]Invalid room id, try again.[/bold red]")
                continue

            break

    player_name = Prompt.ask("[bold]Enter a nickname[/bold]")
    payload = {"room_id": room_id, "player_name": player_name}
    join_resp = requests.post(f"{base_server_url}/rooms/join", json=payload).json()

    if not join_resp["success"]:
        console.print("[bold red]Unable to join the room.[/bold red]")
        console.print(join_resp["message"])
        quit(1)

    console.print("[bold green]Successfully joined the room![/bold green]")
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
                        console.print("[bold]Your turn![/bold]")
                        pos = game.position_input()
                        move = Move(pos, player_name)
                        move_event = Event(EventType.MOVE, {"move": move.asdict()})
                        await ws.send(json.dumps(move_event.asdict()))

                    case EventType.RESULT:
                        game.board = game.board = [
                            list(map(lambda x: Cell(x), row))
                            for row in event.data["board"]
                        ]
                        game.display_board(
                            CheckWinResult.from_dict(event.data["result"])
                        )
                        console.print(f"[bold]{event.data['message']}[/bold]")
                        return

                    case EventType.MESSAGE:
                        console.print(
                            f"[bold yellow]server> {event.data['message']}[/bold yellow]"
                        )

                    case _:
                        raise Exception(f"unknown {event=} recieved from server")

        except KeyboardInterrupt:
            console.print("[bold red]Game interrupted.[/bold red]")
            quit(1)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--server",
        "-s",
        default=DEFAULT_SERVER_IP,
        help="IP address or hostname of the game server",
    )
    return parser.parse_args()


def cli():
    """Entry point for the package."""
    args = parse_args()
    asyncio.run(main(args.server))


if __name__ == "__main__":
    cli()
