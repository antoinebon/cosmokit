import pytest

from cosmic import (
    MemmoryRepository,
    MemmoryUnitOfWork,
)

from .conftest import Telemetry, TelemetryRepository, TelemetryUnitOfWork


def test_malformed_unit_of_work():
    class NonRepository:
        pass

    with pytest.raises(TypeError) as e:

        class BadUnitOfWork(MemmoryUnitOfWork, repository_type=NonRepository):
            pass

    assert str(e.value) == "Repository must inherit from AbstractRepository"

    with pytest.raises(TypeError) as e:
        TelemetryUnitOfWork(MemmoryRepository())
    assert str(e.value) == "Expecting repository of type TelemetryRepository"


def test_unit_of_work():
    tel = Telemetry(message="hello")
    tel2 = Telemetry(message="bye")
    rep = TelemetryRepository([tel])
    uow = TelemetryUnitOfWork(rep, alias="telemetries")

    assert uow.repository == uow.telemetries

    with uow:
        uow.telemetries.add(tel2)

    assert uow.telemetries.get("bye") is None
    assert uow.telemetries.get("hello") is not None

    with uow:
        uow.telemetries.add(tel2)
        uow.commit()

    assert uow.telemetries.get("bye") is not None
    assert uow.telemetries.get("hello") is not None
