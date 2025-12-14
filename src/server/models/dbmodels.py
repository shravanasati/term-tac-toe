from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import DATETIME, Boolean, Column, Enum, String

from .database import Base


class GameStatus(str, PyEnum):
    WAITING = "waiting"
    PLAYING = "playing"
    FINISHED = "finished"
    REMATCH_VOTING = "rematch_voting"


class Room(Base):
    __tablename__ = "rooms"

    room_id = Column(String(6), primary_key=True, index=True, unique=True)
    player1 = Column(String(50), default="")
    player2 = Column(String(50), default="")
    token1 = Column(String(43), default="")
    token2 = Column(String(43), default="")
    # Use Python UTC time to avoid timezone skew between DB server time and app local time.
    created_on = Column(DATETIME, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    game_status = Column(Enum(GameStatus), default=GameStatus.WAITING)
    winner = Column(String(50), default="")
    board_state = Column(String(200), default="---------")
    current_turn = Column(String(50), default="")
