import abc
import copy
from collections.abc import Generator

from ..adapters.repository import AbstractRepository
from ..domain.messages import Event


class AbstractUnitOfWork(abc.ABC):
    _repository_type: type[AbstractRepository]

    def __init__(self, repository: AbstractRepository, alias: str | None = None):
        self._check_repository_type(repository)
        self.repository = repository
        if alias:
            setattr(AbstractUnitOfWork, alias, property(lambda self: self.repository))

    def __init_subclass__(cls, repository_type: type[AbstractRepository] = AbstractRepository, **kwargs):
        if not issubclass(repository_type, AbstractRepository):
            raise TypeError(f"Repository must inherit from {AbstractRepository.__name__}")
        cls._repository_type = repository_type

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}, repository_type={self._repository_type.__name__}>"

    def _check_repository_type(self, repository: AbstractRepository) -> None:
        if not type(repository) == self._repository_type:
            raise TypeError(f"Expecting repository of type {self._repository_type.__name__}")

    def __enter__(self) -> "AbstractUnitOfWork":
        return self

    def __exit__(self, *args) -> None:
        self.rollback()

    def commit(self) -> None:
        self._commit()

    def collect_new_events(self) -> Generator[Event, None, None]:
        for aggregate in self.repository.seen:
            while aggregate.events:
                yield aggregate.events.pop(0)

    @abc.abstractmethod
    def _commit(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self) -> None:
        raise NotImplementedError


class MemmoryUnitOfWork(AbstractUnitOfWork):
    def __enter__(self) -> "MemmoryUnitOfWork":
        self._repo_backup: AbstractRepository = copy.copy(self.repository)
        self._committed: bool = False
        return self

    def _commit(self) -> None:
        self._committed = True

    def rollback(self) -> None:
        if not self._committed:
            self.repository = self._repo_backup
