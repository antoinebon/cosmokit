import json

from pydantic import BaseModel


class Message(BaseModel):
    """
    Immutable entity fully identified by fields values
    """

    class Config:
        frozen: bool = True

    def __hash__(self) -> int:
        return hash(json.dumps(self.__fields__()))


class Command(Message):
    pass


class Event(Message):
    pass
