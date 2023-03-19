import pytest

from cosmic import (
    Aggregate,
    MemmoryRepository,
)

from .conftest import Telemetry, TelemetryRepository


def test_telemetry():
    tel = Telemetry(message="hello")
    assert tel.id is not None


def test_malformed_repository():
    class NonAggregate:
        pass

    with pytest.raises(TypeError) as e:

        class BadRepository(MemmoryRepository, entity_type=NonAggregate):
            pass

    assert str(e.value) == "Entity must inherit from Aggregate"

    with pytest.raises(TypeError) as e:
        rep = TelemetryRepository()
        rep.add(Aggregate())
    assert str(e.value) == "Expecting entity of type Telemetry"


def test_well_formed_repository():
    rep = TelemetryRepository()
    assert rep.match_key == "message"
    assert len(rep.items) == 0

    tel = Telemetry(message="hello")

    rep.add(tel)

    assert rep.get("hello").message == "hello"

    rep = TelemetryRepository([tel])
    assert rep.get("hello").message == "hello"
