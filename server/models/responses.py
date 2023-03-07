from pydantic import BaseModel


class CreateRoomResponse(BaseModel):
    success: bool
    message: str
    room_id: str
