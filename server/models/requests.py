from pydantic import BaseModel


class JoinRoomRequest(BaseModel):
    player_name: str
    room_id: str


class MoveRequest(BaseModel):
    position: int
    player_name: str


class RematchVoteRequest(BaseModel):
    vote: bool
    player_name: str
