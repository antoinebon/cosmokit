from pydantic import validator

from cosmic import (
    Aggregate,
    MemmoryRepository,
    MemmoryUnitOfWork,
)


class Telemetry(Aggregate):
    message: str
    tel_id: int | None = None
    _hash_fields: list[str] = ["tel_id"]

    @validator("tel_id", pre=True, always=True)
    def check_id(cls, tel_id, values):
        return tel_id or hash(values["message"])


class TelemetryRepository(MemmoryRepository, entity_type=Telemetry):
    match_key: str = "message"


class TelemetryUnitOfWork(MemmoryUnitOfWork, repository_type=TelemetryRepository):
    pass
