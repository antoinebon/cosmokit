import pytest

from cosmokit import (
    Aggregate,
)

from .conftest import Telemetry, TelemetryRepository


def test_telemetry():
    tel = Telemetry(message="hello")
    assert hash(tel) is not None


def test_malformed_repository():
    class NonAggregate:
        pass

    with pytest.raises(TypeError) as e:
        rep = TelemetryRepository()
        rep.add(Aggregate())
    assert str(e.value) == "Expecting entity of type Telemetry"


def test_well_formed_repository():
    rep = TelemetryRepository()
    assert len(rep.items) == 0

    tel = Telemetry(message="hello")

    rep.add(tel)

    assert rep.get(message="hello").message == "hello"

    rep = TelemetryRepository([tel])
    assert rep.get(message="hello").message == "hello"
