from cosmokit import (
    Aggregate,
    MemoryRepository,
    MemoryUnitOfWork,
)


class Telemetry(Aggregate):
    message: str
    _hash_fields: list[str] = ["message"]

    # @validator("tel_id", pre=True, always=True)
    # def check_id(cls, tel_id, values):
    #     return tel_id or hash(values["message"])


class TelemetryRepository(MemoryRepository):
    _entity_type = Telemetry


class TelemetryUnitOfWork(MemoryUnitOfWork):
    _repository_type = TelemetryRepository
