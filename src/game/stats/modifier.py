from __future__ import annotations
from typing import ClassVar, TypeAlias, cast, get_args, runtime_checkable

from abc import abstractproperty
from decimal import Decimal
from enum import Enum
from typing import Literal, Protocol

from lib.supports_decimal import SupportsDecimal


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
