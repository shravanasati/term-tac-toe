from pydantic import BaseModel


class CreateRoomResponse(BaseModel):
    success: bool
    message: str
    room_id: str


class JoinRoomResponse(BaseModel):
    success: bool
    message: str
    websocket_redirect: str
    token: str


class RoomStatusResponse(BaseModel):
    success: bool
    message: str
    status: str
    players: list[str]
    current_turn: str
    winner: str


class RematchVoteResponse(BaseModel):
    success: bool
    message: str
    votes: dict[str, bool]
    all_voted: bool
