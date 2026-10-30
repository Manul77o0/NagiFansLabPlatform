from sqlalchemy import Column, Integer, String

from .database import Base


class SystemUser(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=False)
    level = Column(Integer, index=False, default=1)
    email = Column(String, index=False)
    password = Column(String, index=False)
    disabled = Column(Integer, index=False, default=0)