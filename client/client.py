import requests
from rich.prompt import Prompt
from websockets.sync import client

base_server_url = "http://127.0.0.1:8000"
base_server_ws = "ws://127.0.0.1:8000"

# todo add validation for player name, must not be greater than 50 chars
# todo check for websocket redirect url in join room response
# todo commas and symbols not allowed in player name

if __name__ == "__main__":
    prompt_text = "What do you want to do? \n1. Create a room \n2. Join a room\n"
    choice = Prompt.ask(prompt_text, choices=["1", "2"])

    if choice == "1":
        resp = requests.post(f"{base_server_url}/rooms/create")

        if resp.status_code != 200:
            print("Unable to request the server!")
            quit(1)

        resp = resp.json()
        if not resp["success"]:
            print("Cannot create a room.")
            print(resp["message"])
            quit()

        else:
            room_id = resp["room_id"]
            print(f"Room with room id `{room_id}` created successfully.")
            player = Prompt.ask("Enter a nickname")
            payload = {"room_id": room_id, "player_name": player}
            join_req = requests.post(f"{base_server_url}/rooms/join", json=payload).json()
            print(join_req)
            if not join_req["success"]:
                print("Unable to join the room.")
                print(join_req["message"])
                quit(1)

            redirect = join_req["websocket_redirect"]
            token = join_req["token"]
            websocket_url = f"{base_server_ws}{redirect}?token={token}"
            with client.connect(websocket_url) as player:
                # player.send("lmao ded")
                try:
                    while True:
                        print(player.recv())

                except KeyboardInterrupt:
                    quit(1)

    else:
        while True:
            room_id = Prompt.ask("Enter the six-digit room id")
            if len(room_id) != 6:
                print("Invalid room id, try again.")
                continue

            break

        resp = requests.post(f"{base_server_url}/rooms/join", json={"room_id": room_id, "player_name": input("enter nickname: ")})

        if resp.status_code != 200:
            print("Unable to request the server!")
            quit(1)

        resp = resp.json()
        if not resp["success"]:
            print("Cannot join the room.")
            print(resp["message"])
            quit()

        else:
            redirect = resp["websocket_redirect"]
            token = resp["token"]
            websocket_url = f"{base_server_ws}{redirect}?token={token}"
            with client.connect(websocket_url) as player:
                try:
                    while True:
                        print(player.recv())

                except KeyboardInterrupt:
                    quit(1)
            pass
