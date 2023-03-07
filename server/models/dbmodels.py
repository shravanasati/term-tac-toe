from sqlalchemy import Boolean, Column, String, DATETIME
from sqlalchemy.sql.functions import now

from .database import Base


class Room(Base):
    __tablename__ = "rooms"

    room_id = Column(String(6), primary_key=True, index=True, unique=True)
    players = Column(String(100), default="")
    created_on = Column(DATETIME, default=now())
    is_active = Column(Boolean, default=True)
