from cosmic import (
    Aggregate,
    MemmoryRepository,
    MemmoryUnitOfWork,
)
from pydantic import validator


class Telemetry(Aggregate):
    message: str
    id: int = None
    _hash_fields = ['id']

    @validator('id', pre=True, always=True)
    def check_id(cls, id, values):
        return id or hash(values['message'])


class TelemetryRepository(MemmoryRepository, entity_type=Telemetry):
    match_key : str = 'message'


class TelemetryUnitOfWork(MemmoryUnitOfWork, repository_type=TelemetryRepository):
    pass
