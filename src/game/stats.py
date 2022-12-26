from __future__ import annotations

from abc import ABC, abstractmethod, abstractproperty
from contextlib import suppress
from decimal import Decimal
from enum import Enum
from typing import (ClassVar, Literal, Protocol, TypeAlias, cast, get_args, overload,
                    runtime_checkable)

from typing_extensions import override

from lib.assert_never import assert_never
from lib.decimal_tools import DecimalRange, SupportsDecimal
from lib.sentinel import Sentinel
from src.game.xp import ExponentialLevelSystem


@runtime_checkable
class HasValue(Protocol):
    @abstractproperty
    def value(self) -> Decimal: ...


class DynamicValue(HasValue):

    def __init__(self, _dynamic_source: HasValue,
                 _multiplier: SupportsDecimal = Decimal('1.0')) -> None:
        self._dynamic_source = _dynamic_source
        self._multiplier = Decimal(_multiplier)

    @ property
    def value(self) -> Decimal:
        return self._dynamic_source.value * self._multiplier


class ConstValue(HasValue):

    __stored: ClassVar[dict[Decimal, ConstValue]] = {}

    def __init__(self, _value: SupportsDecimal) -> None:
        self._value = Decimal(_value)

    def __new__(cls, _value: SupportsDecimal) -> ConstValue:
        _value = Decimal(_value)

        try:
            return ConstValue.__stored[_value]
        except KeyError:
            instance = object.__new__(cls)
            ConstValue.__init__(instance, _value)
            ConstValue.__stored[_value] = instance

            return instance

    @ property
    def value(self) -> Decimal:
        return self._value


class Modification(Enum):

    FLAT = 1
    PERCENT_ADDITIVE = 2
    PERCENT_MULTIPLICATIVE = 3


Order: TypeAlias = Literal[0, 1, 2, 3, 4, 5]
ORDER_VALUES: tuple[Order, ...] = get_args(Order)


class Modifier(HasValue):

    """
    Modifiers are used to modify values of stats. The order in which modifiers should
    be applied is represented by their `order` values (modifiers with the lower order
    values are supposed to be applied first).

    Modifiers can be of different type, represented by their `modification` type:
        - `FLAT` modifier simply adds its value to the modified object's value.
        - `PERCENT_ADDITIVE` modifiers stack together (assuming they have the same order
        value, which would be true by default), then the modified object's value is
        multiplied by the result sum.
        - `PERCENT_MULTIPLICATIVE` modifier immediately multiplies the modified object's
        value by the modifier's value.

    Note that the value of a percent modifier is added to 1.0 before making the actual
    multiplication.

    ```Python
    stat_ = Stat(_base=10)
    stat_.value
    >>> 10
    stat_.add_modifier(
        Modifier(_base=0.5, _modification=Modification.PERCENT_MULTIPLICATIVE))
    stat_.value
    >>> 15
    ```

    In order to create debuffs, provide modifiers with negative bases.

    ```Python
    stat_ = Stat(_base=10)
    stat_.add_modifier(Modifier(-0.5, Modification.PERCENT_MULTIPLICATIVE))
    stat_.value
    >>> 5
    ```

    A modifier can also take any object with a `value` property as its base. In this case
    this object's value will be used as the modifier's value.

    ```Python
    base = GenericValue(10)
    modifier = Modifier(base, Modification.FLAT)

    modifier.value
    >>> 10

    base.value += 1
    modifier.value
    >>> 11
    ```
        """

    def __init__(self, _base: HasValue | SupportsDecimal, _modification: Modification,
                 _order: Order | None = None,
                 _source: object | None = None) -> None:
        """
        @params
            - _base: The base which defines the modifier's value. If it's an object with
            a `value` property, the modifier's value is equal to this object's value
            and therefore can be updated. If it's a constant, the modifier will always
            return the same value. Negative modifiers (debuffs) are created by making
            the base negative. Percent modifiers work with the actual base value: for
            instance, a percent modifier with the base equal to 0.5 will increase its
            modified object's value by 50% (to 150%).

            - _modification: The type of modification which defines how the value of a
            modified object will be affected.
                - `FLAT` modifier adds the modifier's value to the object's value.
                - `PERCENT_ADDITIVE` modifiers of the same order are summed together and
                then the object's value is multiplied by their result value.
                - `PERCENT_MULTIPLICATIVE` modifier multiplies the object's value by the
                modifier's value.

            - _order: A number from zero to five that determines the order in which the
            modifiers are applied to the modified object (modifiers with the lower order
            are applied first). If not given, the _modification's value is used, where
            `FLAT` is 1, `PERCENT_ADDITIVE` is 2, and `PERCENT_MULTIPLICATIVE` is 3.
            There is usually no need to override the default behaviour.

            - _source: Any object (e.g., a status token) which represents the source the
            modifier comes from.
            """

        self._base = _base if isinstance(
            _base, HasValue) else ConstValue(Decimal(_base))

        self._modification = _modification

        assert self._modification.value in ORDER_VALUES, (
            "Inappropriate modification value, expected to be in"
            f"{str(ORDER_VALUES)}, but became {self._modification.value}.")
        self._order = _order if _order is not None else self._modification.value

        self._source = _source

    @property
    def order(self) -> Order:
        return cast(Order, self._order)

    @property
    def source(self) -> object:
        return self._source

    @property
    def modification(self) -> Modification:
        return self._modification

    @property
    def value(self) -> Decimal:
        return self._base.value


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
                assert_never(modifier.modification)

        return value


class BoundedStat(Stat):

    def __init__(self, _base: SupportsDecimal, _lower_bound: SupportsDecimal | None,
                 _upper_bound: SupportsDecimal | None, _modified_upper_bound: SupportsDecimal | None) -> None:
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

        if self._modified_upper_bound is not None:
            assert self._upper_bound is not None
            if self._modified_upper_bound < self._upper_bound:
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
        if lower_bound is not None:
            value = max(value, lower_bound)
        if upper_bound is not None:
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


# class ResourceDrained(Exception):
#     pass


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

        # self._aware_of_resource_drain = False if self._current > Decimal(
        #     0) else True

    def __str__(self) -> str:
        return f"{self.current}/{self.value}"

    @property
    def current(self) -> Decimal:
        #     # Required because values of modifiers may change.
        self._update_current()
        return self._current

    @current.setter
    def current(self, new_value: SupportsDecimal) -> None:
        self._current = Decimal(new_value)
        # self._update_current()

    @property
    def regeneration(self) -> ResourceRegeneration:
        return self._regeneration

    # @override
    # def add_modifier(self, modifier: Modifier) -> None:
    #     super().add_modifier(modifier)
    #     self._update_current()

    # @override
    # def calculate_value_with_temporary_modifiers(self, temporary_modifiers: list[Modifier]) -> Decimal:
    #     modifiers = self._modifiers + temporary_modifiers
    #     modifiers.sort(key=lambda m: m.order)
    #     value = self._calculate_modified_value(modifiers)

    #     self._current = min(self._current, value)
    #     self._update_current()

    #     return self._adjusted_value(value)

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

    # @override
    # def remove_modifier(self, modifier: Modifier) -> None:
    #     super().remove_modifier(modifier)
        # self._update_current()

    # @override
    # def remove_source(self, source: object) -> None:
    #     super().remove_source(source)
        # self._update_current()

    # @override
    # def _adjust_base(self) -> None:
    #     super()._adjust_base()
        # self._update_current()

    def _update_current(self) -> None:
        self._current = self._adjust_for_bounds(
            self._current, self._lower_bound, self.value)

        # if self._lower_bound is not None \
        #         and self._current <= self._lower_bound \
        #         and not self._aware_of_resource_drain:
        #     self._aware_of_resource_drain = True
        #     raise ResourceDrained

        # if self._lower_bound is not None \
        #         and self._current > self._lower_bound:
        #     self._aware_of_resource_drain = False


class Skill(PrimaryStat, ExponentialLevelSystem):

    def __init__(self, _base: SupportsDecimal, _scale: SupportsDecimal,
                 _lower_bound: SupportsDecimal | None | Sentinel = Sentinel.NOT_GIVEN,
                 _upper_bound: SupportsDecimal | None | Sentinel = Sentinel.NOT_GIVEN,
                 _modified_upper_bound: SupportsDecimal | None | Sentinel = Sentinel.NOT_GIVEN) -> None:
        super().__init__(_base, _lower_bound, _upper_bound, _modified_upper_bound)
        ExponentialLevelSystem.__init__(self, _scale)

    @property
    def level(self) -> int:
        return int(self.base)

    @override
    def add_xp(self, amount: int) -> None:
        if self.is_capped():
            return

        super().add_xp(amount)
        while self.can_levelup():
            self.levelup()

    @override
    def can_levelup(self) -> bool:
        if self.is_capped():
            return False

        return super().can_levelup()

    @override
    def levelup(self) -> None:
        if not self.can_levelup():
            return

        self.base += 1

    @override
    def _set_base(self, new_value: SupportsDecimal) -> None:
        super()._set_base(new_value)
        self._refresh_xp()
