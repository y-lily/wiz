from decimal import Decimal

from src.game.stats.modifier import HasValue


class MockValue(HasValue):

    def __init__(self, _value: Decimal) -> None:
        self._value = _value

    @property
    def value(self) -> Decimal:
        return self._value

    @value.setter
    def value(self, new_value: Decimal) -> None:
        self._value = new_value
