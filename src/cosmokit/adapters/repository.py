import abc

from ..domain.model import Aggregate


class AbstractRepository(abc.ABC):
    _entity_type: type[Aggregate]

    def __init__(self):
        self.seen = set()

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


class MemoryRepository(AbstractRepository):
    def __init__(self, items: list[Aggregate] | None = None):
        super().__init__()
        self.items = {hash(item): item for item in items} if items else {}

    def __copy__(self):
        return type(self)(items=list(self.items.values()))

    def _add(self, aggregate: Aggregate) -> None:
        self.items[hash(aggregate)] = aggregate

    def _get(self, *args, **kwargs) -> Aggregate | None:
        key = self._entity_type.hash_from_kwargs(**kwargs)
        return self.items.get(key)
