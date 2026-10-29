from sqlalchemy import Column, Integer, String

from .database import Base


class User(Base):
    """Represent a user stored in the database.

    Attributes
    ----------
    id : int
        The user's primary key.
    name : str
        The user's name.
    level : int
        The user's level.
    email : str
        The user's email.
    password : str
        The user's password.(hashed)
    disabled : int
        The user's disabled status.

    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=False)
    level = Column(Integer, index=False, default=1)
    email = Column(String, index=False)
    password = Column(String, index=False)
    disabled = Column(Integer, index=False, default=0)