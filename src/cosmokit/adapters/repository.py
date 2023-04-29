import abc

from ..domain.model import Aggregate


class AbstractRepository(abc.ABC):
    _aggregate_type: type[Aggregate]

    def __init__(self):
        self.seen = set()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}, aggregate_type={self._aggregate_type.__name__}>"

    def _check_aggregate_type(self, aggregate: Aggregate) -> None:
        if not type(aggregate) == self._aggregate_type:
            raise TypeError(f"Expecting aggregate of type {self._aggregate_type.__name__}")

    def add(self, aggregate: Aggregate) -> None:
        self._check_aggregate_type(aggregate)
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
    _items: dict[int, Aggregate]

    def __init__(self, items: list[Aggregate] | None = None):
        super().__init__()
        self._items = {hash(item): item for item in items} if items else {}

    def __copy__(self):
        return type(self)(items=list(self._items.values()))

    def _add(self, aggregate: Aggregate) -> None:
        self._items[hash(aggregate)] = aggregate

    def _get(self, *args, **kwargs) -> Aggregate | None:
        key = self._aggregate_type.hash_from_kwargs(**kwargs)
        return self._items.get(key)
