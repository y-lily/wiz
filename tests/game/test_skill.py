from decimal import Decimal

import pytest

from src.game.stats.skill import Skill


class TestSkill:

    @pytest.fixture
    def stealth(self) -> Skill:
        return Skill(_base=0, _scale=Decimal('1.4'))

    @pytest.fixture
    def xp_at_level_one(self) -> int:
        return 144

    def test_adding_xp_levelups_automatically(self, stealth: Skill, xp_at_level_one: int) -> None:
        stealth.add_xp(xp_at_level_one - stealth._xp_points)
        assert stealth.level == 1

    def test_manual_levelup_does_not_work_if_not_enough_xp(self, stealth: Skill) -> None:
        stealth.levelup()
        assert stealth.level == 0

    def test_increasing_base_adjusts_xp(self, stealth: Skill, xp_at_level_one: int) -> None:
        stealth.base += 1
        assert stealth._xp_points == xp_at_level_one

    def test_increasing_base_increases_level(self, stealth: Skill) -> None:
        stealth.base += 1
        assert stealth.level == 1

    def test_decreasing_base_adjusts_xp(self, stealth: Skill, xp_at_level_one: int) -> None:
        stealth.base += 2
        stealth.base -= 1
        assert stealth._xp_points == xp_at_level_one

    def test_adding_negative_xp_raises_value_error(self, stealth: Skill) -> None:
        with pytest.raises(ValueError):
            stealth.add_xp(-1)

    def test_adding_zero_xp_does_not_raise_error(self, stealth: Skill) -> None:
        stealth.add_xp(0)
