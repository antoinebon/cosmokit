import json

from pydantic import BaseModel

from .messages import Event


class Entity(BaseModel):
    """
    Mutable entity fully identified by its hash
    """

    _hash_fields: list[str]

    class Config:
        arbitrary_types_allowed: bool = True

    @classmethod
    def hash_from_kwargs(cls, **kwargs) -> int:
        return hash(json.dumps({a: kwargs[a] for a in cls._hash_fields}))

    def __hash__(self) -> int:
        return hash(json.dumps({a: getattr(self, a) for a in self._hash_fields}))

    def __eq__(self, other) -> bool:
        if not isinstance(other, type(self)):
            return False
        return hash(other) == hash(self)


class ValueObject(BaseModel):
    """
    Immutable entity fully identified by fields values
    """

    class Config:
        frozen: bool = True

    def __hash__(self) -> int:
        return hash(json.dumps(self.__fields__()))


class Aggregate(Entity):
    """
    Implements bounded context

    Entrypoint to changing the state of the bounded context Implement all
    operation to change the state of the bounded context here

    What aggregate should we use for our system? The choice is somewhat
    arbitrary, but it`s important. The aggregate will be the boundary where we
    make sure every operation ends in a consistent state. This helps us to
    reason about our software and prevent weird race issues. We want to draw a
    boundary around a small number of objects—the smaller, the better, for
    performance—that have to be consistent with one another, and we need to
    give this boundary a good name.

    One Aggregate = One Repository

    Once you define certain entities to be aggregates, we need to apply the
    rule that they are the only entities that are publicly accessible to the
    outside world. In other words, the only repositories we are allowed should
    be repositories that return aggregates.

    Note: The rule that repositories should only return aggregates is the main
    place where we enforce the convention that aggregates are the only way into
    our domain model. Be wary of breaking it!
    """

    events: list[Event] = []

    def add_event(self, event: Event) -> None:
        self.events.append(event)
