from pydantic import validator

from cosmic import (
    Aggregate,
    MemmoryRepository,
    MemmoryUnitOfWork,
)


class Telemetry(Aggregate):
    message: str
    tel_id: int
    _hash_fields = ["tel_id"]

    @validator("tel_id", pre=True, always=True)
    def check_id(self, tel_id, values):
        return tel_id or hash(values["message"])


class TelemetryRepository(MemmoryRepository, entity_type=Telemetry):
    match_key: str = "message"


class TelemetryUnitOfWork(MemmoryUnitOfWork, repository_type=TelemetryRepository):
    pass
