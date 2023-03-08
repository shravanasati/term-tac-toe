from pydantic import BaseModel


class JoinRoomRequest(BaseModel):
    player_name: str
    room_id: str
