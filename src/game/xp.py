from abc import ABC, abstractmethod, abstractproperty
from decimal import Decimal

from lib.decimal_tools import SupportsDecimal


class ExponentialLevelSystem(ABC):

    def __init__(self, _scale: SupportsDecimal) -> None:
        self._scale = Decimal(_scale)
        self._xp_points = 0
        self._refresh_xp()

    @abstractproperty
    def level(self) -> int:
        pass

    def add_xp(self, amount: int) -> None:
        if amount < 0:
            raise ValueError(
                f"Expected to get non-negative xp but got {amount}.")
        self._xp_points += amount

    def can_levelup(self) -> bool:
        return self._xp_points >= self._calculate_xp_at_level(self.level + 1)

    @abstractmethod
    def levelup(self) -> None:
        pass

    def _calculate_xp_at_level(self, level: int) -> int:
        # ((kx)^3.5) + (1.18^x) + (100kx)
        k = self._scale
        return int(((k * level) ** Decimal('3.5')) + (Decimal('1.18') ** level) + (k * 100 * level))

    def _refresh_xp(self) -> None:
        xp_for_current_level = self._calculate_xp_at_level(self.level)
        xp_for_next_level = self._calculate_xp_at_level(self.level + 1)

        if not xp_for_current_level <= self._xp_points < xp_for_next_level:
            self._xp_points = xp_for_current_level
