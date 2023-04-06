from sqlalchemy import DATETIME, Boolean, Column, String
from sqlalchemy.sql.functions import now

from .database import Base


class Room(Base):
    __tablename__ = "rooms"

    room_id = Column(String(6), primary_key=True, index=True, unique=True)
    player1 = Column(String(50), default="")
    player2 = Column(String(50), default="")
    token1 = Column(String(43), default="")
    token2 = Column(String(43), default="")
    created_on = Column(DATETIME, default=now())
    is_active = Column(Boolean, default=True)
