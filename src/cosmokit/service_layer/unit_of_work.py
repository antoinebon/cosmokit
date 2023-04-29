from __future__ import annotations

import abc
import copy
from collections.abc import Generator

from ..adapters.repository import AbstractRepository, MemoryRepository
from ..domain.model import Event


class AbstractUnitOfWork(abc.ABC):
    _repository_type: type[AbstractRepository]
    repository: AbstractRepository

    def __init__(self, repository: AbstractRepository):
        self._check_repository_type(repository)
        self.repository = repository

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}, repository_type={self._repository_type.__name__}>"

    def _check_repository_type(self, repository: AbstractRepository) -> None:
        if not type(repository) == self._repository_type:
            raise TypeError(f"Expecting repository of type {self._repository_type.__name__}")

    def __enter__(self) -> AbstractUnitOfWork:
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


class MemoryUnitOfWork(AbstractUnitOfWork):
    _repository_type = MemoryRepository
    _committed: bool
    _repo_backup: AbstractRepository

    def __enter__(self) -> MemoryUnitOfWork:
        self._repo_backup = copy.copy(self.repository)
        self._committed = False
        return self

    def _commit(self) -> None:
        self._committed = True

    def rollback(self) -> None:
        if not self._committed:
            self.repository = self._repo_backup
