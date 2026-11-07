import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from .database import Base


def get_jst_now():
    JST = datetime.timezone(datetime.timedelta(hours=9))
    return datetime.datetime.now(JST).replace(tzinfo=None)

class SystemUser(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=False)
    level = Column(Integer, index=False, default=1)  # 1: Read 2: Write 3: Manage
    email = Column(String, index=False, unique=True)
    password = Column(String, index=False)
    disabled = Column(Integer, index=False, default=0)
    updated_at = Column(DateTime, index=False, default=get_jst_now, onupdate=get_jst_now)

class WireGuard(Base):
    
    __tablename__ = "wireguard"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, index=False)
    name = Column(String, index=False)
    value = Column(Text, index=False)
    updated_at = Column(DateTime, index=False, default=get_jst_now, onupdate=get_jst_now)