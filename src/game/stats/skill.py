from typing_extensions import override

from lib.decimal_tools import SupportsDecimal
from lib.sentinel import Sentinel
from src.game.stats.stat_ import PrimaryStat
from src.game.xp import ExponentialLevelSystem


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
