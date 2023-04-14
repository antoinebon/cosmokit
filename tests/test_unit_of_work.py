import pytest

from cosmokit import (
    MemoryRepository,
)

from .conftest import Telemetry, TelemetryRepository, TelemetryUnitOfWork


def test_malformed_unit_of_work():
    class NonRepository:
        pass

    with pytest.raises(TypeError) as e:
        TelemetryUnitOfWork(MemoryRepository())
    assert str(e.value) == "Expecting repository of type TelemetryRepository"


def test_unit_of_work():
    tel = Telemetry(message="hello")
    tel2 = Telemetry(message="bye")
    rep = TelemetryRepository([tel])
    uow = TelemetryUnitOfWork(rep)

    with uow:
        uow.repository.add(tel2)

    assert uow.repository.get(message="bye") is None
    assert uow.repository.get(message="hello") is not None

    with uow:
        uow.repository.add(tel2)
        uow.commit()

    assert uow.repository.get(message="bye") is not None
    assert uow.repository.get(message="hello") is not None
