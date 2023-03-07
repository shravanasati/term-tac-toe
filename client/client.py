import requests
from rich.prompt import Prompt


base_server_url = "https://127.0.0.1:8000"

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
            # websocket here
            print("Waiting for another player to join...")

    else:
        while True:
            room_id = Prompt.ask("Enter the six-digit room id")
            if len(room_id) != 6:
                print("Invalid room id, try again.")
                continue

            break

        resp = requests.post(f"{base_server_url}/rooms/join", data={"room_id": room_id})

        if resp.status_code != 200:
            print("Unable to request the server!")
            quit(1)

        resp = resp.json()
        if not resp["success"]:
            print("Cannot join the room.")
            print(resp["message"])
            quit()

        else:
            # websocket here
            pass
