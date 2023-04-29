import json
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class Entity:
    """
    Mutable entity fully identified by its hash
    """

    _hash_fields: ClassVar[list[str]]

    @classmethod
    def hash_from_kwargs(cls, **kwargs) -> int:
        for f in cls._hash_fields:
            if f not in kwargs:
                raise Exception(f"{cls.__name__}.get_hash requires a value for {f}")
        return hash(json.dumps([hash(kwargs[a]) for a in cls._hash_fields]))

    def __hash__(self) -> int:
        return hash(json.dumps([hash(getattr(self, a)) for a in self._hash_fields]))

    def __eq__(self, other) -> bool:
        if not isinstance(other, type(self)):
            return False
        return hash(other) == hash(self)


@dataclass(frozen=True)
class ValueObject:
    pass


@dataclass(frozen=True)
class Message(ValueObject):
    pass


@dataclass(frozen=True)
class Command(Message):
    pass


@dataclass(frozen=True)
class Event(Message):
    pass


@dataclass(eq=False)
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

    events: list[Event] = field(init=False, default_factory=list)

    def add_event(self, event: Event) -> None:
        self.events.append(event)
