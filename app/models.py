from database import Base
from sqlalchemy import Column, Integer, String


class User(Base):
    """Represent a user stored in the database.

    Attributes
    ----------
    id : int
        The user's primary key.
    name : str
        The user's name.

    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
