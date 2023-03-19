import abc
from collections.abc import Hashable

from ..domain.model import Aggregate


class AbstractRepository(abc.ABC):
    _entity_type: type[Aggregate]

    def __init__(self):
        self.seen = set()

    def __init_subclass__(cls, entity_type: type[Aggregate] = Aggregate, **kwargs):
        if not issubclass(entity_type, Aggregate):
            raise TypeError(f"Entity must inherit from {Aggregate.__name__}")
        cls._entity_type = entity_type

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}, entity_type={self._entity_type.__name__}>"

    def _check_entity_type(self, entity: type[Aggregate]) -> None:
        if not type(entity) == self._entity_type:
            raise TypeError(f"Expecting entity of type {self._entity_type.__name__}")

    def add(self, aggregate: Aggregate) -> None:
        self._check_entity_type(aggregate)
        self._add(aggregate)
        self.seen.add(aggregate)

    def get(self, *args, **kwargs) -> Aggregate | None:
        aggregate = self._get(*args, **kwargs)
        if aggregate:
            self.seen.add(aggregate)
        return aggregate

    @abc.abstractmethod
    def _add(self, aggregate: Aggregate) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, *args, **kwargs) -> Aggregate | None:
        raise NotImplementedError


class MemmoryRepository(AbstractRepository):
    match_key: str = ""

    def __init__(self, items: list[Aggregate] | None = None, match_key: str | None = None):
        super().__init__()
        self.match_key = match_key or self.match_key
        self.items = {getattr(item, self.match_key): item for item in (items or [])}

    def __copy__(self):
        return type(self)(items=list(self.items.values()), match_key=self.match_key)

    def _add(self, item: Aggregate) -> None:
        self.items[getattr(item, self.match_key)] = item

    def _get(self, key: Hashable) -> Aggregate | None:
        return self.items.get(key)
