from dataclasses import dataclass
from typing import ClassVar

from cosmokit import (
    Aggregate,
    MemoryRepository,
    MemoryUnitOfWork,
)


@dataclass(eq=False)
class Telemetry(Aggregate):
    message: str
    _hash_fields: ClassVar[list[str]] = ["message"]


class TelemetryRepository(MemoryRepository):
    _aggregate_type = Telemetry


class TelemetryUnitOfWork(MemoryUnitOfWork):
    _repository_type = TelemetryRepository
