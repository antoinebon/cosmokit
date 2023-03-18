from uuid import UUID, uuid4

import pytest
from cosmic.domain.messages import Event
from cosmic.domain.model import Aggregate, Entity, ValueObject
from pydantic import validator

# Aggregates consist of one or more child entities
# We need an aggregate root to create an aggregate
# Aggregates capture domain events


class ConstraintViolation(Exception):
    pass


class ValidationError(Exception):
    pass


class Suite(Entity):
    number: str
    name: str
    floor: int
    sqft: int
    leased: bool

    _hash_fields = ['number']

    def lease(self) -> None:
        if self.leased:
            raise ConstraintViolation('Suite is already leased')
        self.leased = True

    def make_available(self) -> None:
        if not self.leased:
            raise ConstraintViolation('Suite is already available')
        self.leased = False


class Address(ValueObject):
    """Address value object"""

    street_line_1: str
    locality: str
    region: str
    postal_code: str
    country_code_iso_alpha_3: str
    street_line_2: str | None = None

    @validator('country_code_iso_alpha_3')
    def check_country_code(cls, country_code_iso_alpha_3: str) -> str:
        if len(country_code_iso_alpha_3) != 3:
            raise ValueError('Country code is expected to be of len')

        country_code_iso_alpha_3 = country_code_iso_alpha_3.upper()
        if country_code_iso_alpha_3 not in ['AUS', 'CAN', 'CYM', 'LCA', 'RWA', 'USA']:
            raise ValueError(f'Country {country_code_iso_alpha_3!r} is not supported')
        return country_code_iso_alpha_3


class SuiteAdded(Event):
    building_id: UUID
    number: str


class SuiteLeased(SuiteAdded):
    pass


class SuiteMadeAvailable(SuiteAdded):
    pass


class SuiteRemoved(Event):
    building_id: UUID
    number: str
    name: str = None


class Building(Aggregate):
    name: str
    address: Address
    suites: list[Suite]
    id: UUID = None

    @validator('id', pre=True, always=True)
    def check_id(cls, id) -> UUID:
        return id or uuid4()

    @property
    def suites_dict(self) -> dict[UUID, Suite]:
        return {s.number: s for s in self.suites}

    def get_suite(self, suite: Suite) -> Suite:
        suite = self.suites_dict.get(suite.number)
        if not suite:
            raise ValueError(f'Suite {suite!r} does not exist')

        return suite

    def add_suite(self, suite: Suite):
        if suite.number not in self.suites:
            self.suites.append(suite)
            self.add_event(SuiteAdded(building_id=self.id, number=suite.number))
        else:
            raise ConstraintViolation('Suite already exists; update if need be')

    def lease_suite(self, suite: Suite):
        suite = self.get_suite(suite)
        suite.lease()
        self.add_event(SuiteLeased(building_id=self.id, number=suite.number))

    def make_suite_available(self, suite: Suite):
        suite = self.get_suite(suite)
        suite.make_available()
        self.add_event(SuiteMadeAvailable(building_id=self.id, number=suite.number))

    def remove_suite(self, suite: Suite):
        if suite.number not in self.suites_dict:
            raise ValueError(f'Suite {suite!r} does not exist')
        self.suites = [s for s in self.suites if s.number != suite.number]
        self.add_event(
            SuiteRemoved(
                building_id=self.id,
                name=suite.name,
                number=suite.number,
            )
        )


def test_value_object():
    address1 = Address(
        street_line_1='30 Rockefeller Plaza',
        locality='New York',
        region='NY',
        postal_code='10111',
        country_code_iso_alpha_3='USA',
    )
    address2 = Address(
        street_line_1='30 Rockefeller Plaza',
        locality='New York',
        region='NY',
        postal_code='10111',
        country_code_iso_alpha_3='USA',
    )
    address3 = Address(
        street_line_1='12 Rockefeller Plaza',
        locality='New York',
        region='NY',
        postal_code='10111',
        country_code_iso_alpha_3='USA',
    )
    assert address1 == address2
    assert address1 != address3


def test_entity():
    suite_a = Suite(
        number='6700', name='Top of the Rock', floor=67, sqft=755602, leased=True
    )
    suite_b = Suite(number='6700', name='Suite 6700', floor=67, sqft=755602, leased=True)
    suite_c = Suite(number='6701', name='Suite 6700', floor=67, sqft=755602, leased=True)
    assert suite_a == suite_b
    assert suite_a != suite_c


def test_aggregate():
    # Create instance of building and its child entities/VOs
    address = Address(
        street_line_1='30 Rockefeller Plaza',
        locality='New York',
        region='NY',
        postal_code='10111',
        country_code_iso_alpha_3='USA',
    )

    suite_a = Suite(
        number='6700', name='Top of the Rock', floor=67, sqft=755602, leased=True
    )
    suite_b = Suite(number='1280', name='Suite 1289', floor=12, sqft=1995, leased=True)

    thirty_rock = Building(
        name='30 Rockefeller Center',
        address=address,
        suites=[suite_a, suite_b],
    )

    # Test domain events
    with pytest.raises(ConstraintViolation):
        thirty_rock.lease_suite(suite_a)

    thirty_rock.make_suite_available(suite_b)

    suite_c = Suite(number='1735', name='Suite 1735', floor=17, sqft=1735, leased=False)
    thirty_rock.add_suite(suite_c)

    thirty_rock.lease_suite(suite_c)

    suite_d = Suite(
        number='109', name='Lobby Concessions', floor=1, sqft=144, leased=False
    )
    thirty_rock.add_suite(suite_d)

    thirty_rock.remove_suite(suite_d)

    # We expect five domain events
    event_iter = iter(thirty_rock.events)

    event_1 = next(event_iter)
    event_2 = next(event_iter)
    event_3 = next(event_iter)
    event_4 = next(event_iter)
    event_5 = next(event_iter)

    assert event_5.name == 'Lobby Concessions'
    assert event_5.number == '109'

    # Now there shouldn't be any more events

    with pytest.raises(StopIteration):
        next(event_iter)

    assert isinstance(event_1, SuiteMadeAvailable)
    assert isinstance(event_2, SuiteAdded)
    assert isinstance(event_3, SuiteLeased)
    assert isinstance(event_4, SuiteAdded)
    assert isinstance(event_5, SuiteRemoved)
