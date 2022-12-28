import random
from decimal import Decimal, DecimalTuple
from typing import TypeAlias

SupportsDecimal: TypeAlias = Decimal | str | int | float | DecimalTuple


def roll_decimal(minimum: Decimal, maximum: Decimal, digits: int = 2) -> Decimal:
    assert digits >= 0

    comma_shift: int = 10 ** digits
    min_ = int(minimum * comma_shift)
    max_ = int(maximum * comma_shift)

    return Decimal(random.randint(min_, max_)) / comma_shift


class DecimalRange:

    def __init__(self, _lower: SupportsDecimal, _upper: SupportsDecimal):
        self._lower = Decimal(_lower)
        self._upper = Decimal(_upper)
        self._adjust_order()

    @property
    def lower(self) -> Decimal:
        return self._lower

    @lower.setter
    def lower(self, new_value: SupportsDecimal) -> None:
        self._lower = Decimal(new_value)
        self._adjust_order()

    @property
    def upper(self) -> Decimal:
        return self._upper

    @upper.setter
    def upper(self, new_value: SupportsDecimal) -> None:
        self._upper = Decimal(new_value)
        self._adjust_order()

    def get_random_value(self) -> Decimal:
        return roll_decimal(self.lower, self.upper)

    def _adjust_order(self) -> None:
        if self._lower > self._upper:
            self._lower, self._upper = self._upper, self._lower
