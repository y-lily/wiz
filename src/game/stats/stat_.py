from abc import ABC, abstractmethod
from contextlib import suppress
from decimal import Decimal
from enum import Enum
from typing import ClassVar

from typing_extensions import override

from lib.sentinel import Sentinel
from lib.decimal_tools import DecimalRange, SupportsDecimal
from src.game.stats.modifier import HasValue, Modification, Modifier


class Stat(HasValue, ABC):

    def __init__(self, _base: SupportsDecimal) -> None:
        self._base = Decimal(_base)
        self._modifiers: list[Modifier] = []

    @property
    def base(self) -> Decimal:
        return self._base

    @base.setter
    def base(self, new_value: SupportsDecimal) -> None:
        self._set_base(Decimal(new_value))

    @property
    def modifiers(self) -> tuple[Modifier, ...]:
        return tuple(self._modifiers)

    @property
    def value(self) -> Decimal:
        value = self._calculate_modified_value(self._modifiers)
        return self._adjusted_value(value)

    def calculate_value_with_temporary_modifiers(self, temporary_modifiers: list[Modifier]) -> Decimal:
        modifiers = self._modifiers + temporary_modifiers
        modifiers.sort(key=lambda m: m.order)
        value = self._calculate_modified_value(modifiers)
        return self._adjusted_value(value)

    def add_modifier(self, modifier: Modifier) -> None:
        self._modifiers.append(modifier)
        self._modifiers.sort(key=lambda m: m.order)

    def remove_modifier(self, modifier: Modifier) -> None:
        self._modifiers.remove(modifier)

    def remove_source(self, source: object) -> None:
        self._modifiers = [
            modifier for modifier in self._modifiers if modifier.source != source]

    @abstractmethod
    def _adjusted_value(self, value: Decimal) -> Decimal:
        return value

    @abstractmethod
    def _set_base(self, new_value: SupportsDecimal) -> None:
        self._base = Decimal(new_value)

    def _calculate_modified_value(self, modifiers: list[Modifier]) -> Decimal:
        value = self.base
        sum_percent_additive = Decimal(0)

        for i, modifier in enumerate(modifiers):
            if modifier.modification is Modification.FLAT:
                value += modifier.value

            elif modifier.modification is Modification.PERCENT_ADDITIVE:
                sum_percent_additive += modifier.value

                # Keep increasing the sum while there are percent additive modifiers.
                with suppress(IndexError):
                    if modifiers[i+1].modification is Modification.PERCENT_ADDITIVE:
                        continue

                value *= Decimal(1) + sum_percent_additive
                sum_percent_additive = Decimal(0)

            elif modifier.modification is Modification.PERCENT_MULTIPLICATIVE:
                value *= Decimal(1) + modifier.value

            else:
                raise ValueError(f"Unexpected modifier type {modifier.type_}")

        return value


class BoundedStat(Stat):

    def __init__(self, _base: SupportsDecimal, _lower_bound: SupportsDecimal | None, _upper_bound: SupportsDecimal | None, _modified_upper_bound: SupportsDecimal | None) -> None:
        if _upper_bound is None and _modified_upper_bound is not None:
            raise ValueError(
                "Stat upper bound cannot be None type if modified upper bound is given.")

        super().__init__(_base)
        self._lower_bound = _lower_bound if _lower_bound is None else Decimal(
            _lower_bound)
        self._upper_bound = _upper_bound if _upper_bound is None else Decimal(
            _upper_bound)
        self._modified_upper_bound = _modified_upper_bound if _modified_upper_bound is None else Decimal(
            _modified_upper_bound)

        if any([not self._lower_bound is None and self._base < self._lower_bound,
                not self._upper_bound is None and self._base > self._upper_bound]):
            raise ValueError(f"Stat base is out of bounds (expected the base to be in "
                             f"[{self._lower_bound}-{self._upper_bound}] range, got {self._base} instead.")

        if self._modified_upper_bound is not None and self._modified_upper_bound < self._upper_bound:
            raise ValueError("Modified upper bound cannot be less than upper bound"
                             f"(Got modified = {_modified_upper_bound}, standard = {_upper_bound})")

    def is_capped(self) -> bool:
        return self._upper_bound is not None and self._base >= self._upper_bound

    def _adjust_base(self) -> None:
        self._base = self._adjust_for_bounds(
            self._base, self._lower_bound, self._upper_bound)

    @override
    def _adjusted_value(self, value: Decimal) -> Decimal:
        return self._adjust_for_bounds(value, self._lower_bound, self._modified_upper_bound)

    def _adjust_for_bounds(self, value: Decimal, lower_bound: Decimal | None, upper_bound: Decimal | None) -> Decimal:
        with suppress(TypeError):
            value = max(value, lower_bound)
        with suppress(TypeError):
            value = min(value, upper_bound)
        return value

    @override
    def _set_base(self, new_value: SupportsDecimal) -> None:
        super()._set_base(Decimal(new_value))
        self._adjust_base()


class PrimaryStat(BoundedStat):

    _LOWER_BOUND_DEFAULT: ClassVar = Decimal(0)
    _UPPER_BOUND_DEFAULT: ClassVar = Decimal(100)
    _MODIFIED_UPPER_BOUND_DEFAULT: ClassVar = Decimal(125)

    def __init__(self, _base: SupportsDecimal, _lower_bound: SupportsDecimal | None | Sentinel = Sentinel.NOT_GIVEN,
                 _upper_bound: SupportsDecimal | None | Sentinel = Sentinel.NOT_GIVEN,
                 _modified_upper_bound: SupportsDecimal | None | Sentinel = Sentinel.NOT_GIVEN) -> None:
        _lower_bound = self._LOWER_BOUND_DEFAULT if _lower_bound is Sentinel.NOT_GIVEN else _lower_bound
        _upper_bound = self._UPPER_BOUND_DEFAULT if _upper_bound is Sentinel.NOT_GIVEN else _upper_bound
        _modified_upper_bound = self._MODIFIED_UPPER_BOUND_DEFAULT if _modified_upper_bound is Sentinel.NOT_GIVEN else _modified_upper_bound

        super().__init__(_base, _lower_bound, _upper_bound, _modified_upper_bound)


class SecondaryStat(BoundedStat):

    def __init__(self, _base: SupportsDecimal, _lower_bound: SupportsDecimal | None = Decimal(0),
                 _upper_bound: SupportsDecimal | None = None,
                 _modified_upper_bound: SupportsDecimal | None = None) -> None:

        super().__init__(_base, _lower_bound, _upper_bound, _modified_upper_bound)


class Resist(SecondaryStat):

    def __init__(self, _base: SupportsDecimal, _base_max: SupportsDecimal | None = None,
                 _growth: SupportsDecimal = Decimal(0), _growth_max: SupportsDecimal = Decimal(0)) -> None:

        _base = DecimalRange(_base, _base_max).get_random_value(
        ) if _base_max is not None else Decimal(_base)
        super().__init__(_base, _lower_bound=Decimal(0), _upper_bound=None)
        self._growth = DecimalRange(_growth, _growth_max)

        if self._growth.lower < 0 or self._growth.upper < 0:
            raise ValueError("Growth value cannot be less than zero.")

    def grow(self) -> Decimal:
        before = self.base
        self.base += self._growth.get_random_value()
        after = self.base

        assert after - before >= 0
        return after - before


class LoadStatus(Enum):

    WHITE = 1
    BLUE = 2
    GREEN = 3
    YELLOW = 4
    RED = 5


class CarryingCapacity(BoundedStat):

    __LOAD_LEVELS: ClassVar = {
        Decimal('1.0'): LoadStatus.RED,
        Decimal('0.8'): LoadStatus.YELLOW,
        Decimal('0.6'): LoadStatus.GREEN,
        Decimal('0.4'): LoadStatus.BLUE,
        Decimal('0.0'): LoadStatus.WHITE,
    }

    def __init__(self, _base: SupportsDecimal) -> None:
        super().__init__(_base, _lower_bound=Decimal(0),
                         _upper_bound=None, _modified_upper_bound=None)
        self._load = Decimal(0)

    def __str__(self) -> str:
        return f"{self.load}/{self.value} lb"

    @property
    def load(self) -> Decimal:
        return self._load

    @load.setter
    def load(self, new_value: SupportsDecimal) -> None:
        self._load = self._adjusted_value(Decimal(new_value))

    @property
    def load_status(self) -> LoadStatus:
        if self.value == Decimal(0):
            return LoadStatus.RED if self.load > Decimal(0) else LoadStatus.WHITE

        load_percent = self.load / self.value

        assert self.load >= Decimal(0)
        # Ensure the dictionary is sorted from max to min.
        assert list(self.__LOAD_LEVELS.keys()) == list(
            sorted(self.__LOAD_LEVELS.keys()))[::-1]

        return next((load_status for step, load_status in self.__LOAD_LEVELS.items() if load_percent >= step), LoadStatus.WHITE)


class ResourceRegeneration(SecondaryStat):

    def __init__(self, _base: SupportsDecimal) -> None:
        super().__init__(_base, _lower_bound=Decimal(0),
                         _upper_bound=None, _modified_upper_bound=None)


class ResourceDrained(Exception):
    pass


class Resource(SecondaryStat):

    def __init__(self, _base: SupportsDecimal, _base_max: SupportsDecimal | None = None,
                 _regeneration: SupportsDecimal | ResourceRegeneration = Decimal(
                     0),
                 _growth: SupportsDecimal = Decimal(0), _growth_max: SupportsDecimal = Decimal(0),
                 _lower_bound: SupportsDecimal | None = Decimal(0), _upper_bound: SupportsDecimal | None = None, _modified_upper_bound: SupportsDecimal | None = None) -> None:

        _base = DecimalRange(_base, _base_max).get_random_value(
        ) if _base_max is not None else Decimal(_base)
        super().__init__(_base, _lower_bound, _upper_bound, _modified_upper_bound)
        self._growth = DecimalRange(_growth, _growth_max)
        self._regeneration = _regeneration if isinstance(
            _regeneration, ResourceRegeneration) else ResourceRegeneration(_regeneration)
        self._current = self._base

        self._aware_of_resource_drain = False if self._current > Decimal(
            0) else True

    def __str__(self) -> str:
        return f"{self.current}/{self.value}"

    @property
    def current(self) -> Decimal:
        # Required because values of modifiers may change.
        self._update_current()
        return self._current

    @current.setter
    def current(self, new_value: SupportsDecimal) -> None:
        self._current = Decimal(new_value)
        self._update_current()

    @property
    def regeneration(self) -> ResourceRegeneration:
        return self._regeneration

    @override
    def add_modifier(self, modifier: Modifier) -> None:
        super().add_modifier(modifier)
        self._update_current()

    @override
    def calculate_value_with_temporary_modifiers(self, temporary_modifiers: list[Modifier]) -> Decimal:
        modifiers = self._modifiers + temporary_modifiers
        modifiers.sort(key=lambda m: m.order)
        value = self._calculate_modified_value(modifiers)

        self._current = min(self._current, value)
        self._update_current()

        return self._adjusted_value(value)

    def grow(self) -> Decimal:
        before = self.base
        self.base += self._growth.get_random_value()
        after = self.base

        assert after - before >= 0

        return after - before

    def regenerate(self) -> Decimal:
        before = self.current
        self.current += self.regeneration.value
        after = self.current

        assert after - before >= 0

        return after - before

    @override
    def remove_modifier(self, modifier: Modifier) -> None:
        super().remove_modifier(modifier)
        self._update_current()

    @override
    def remove_source(self, source: object) -> None:
        super().remove_source(source)
        self._update_current()

    @override
    def _adjust_base(self) -> None:
        super()._adjust_base()
        self._update_current()

    def _update_current(self) -> None:
        self._current = self._adjust_for_bounds(
            self._current, self._lower_bound, self.value)

        if self._lower_bound is not None \
                and self._current <= self._lower_bound \
                and not self._aware_of_resource_drain:
            self._aware_of_resource_drain = True
            raise ResourceDrained

        if self._lower_bound is not None \
                and self._current > self._lower_bound:
            self._aware_of_resource_drain = False
