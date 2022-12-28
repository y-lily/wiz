# from contextlib import suppress
from decimal import Decimal, DecimalTuple
from typing import Any

import pytest
from pytest_lazyfixture import lazy_fixture
from pytest_mock import MockFixture

from src.game.stats import (BoundedStat, CarryingCapacity, ConstValue,
                            DynamicValue, SupportsGetValue, LoadStatus, Modification,
                            Modifier, Resist, Resource, Skill, Stat)
# from src.game.stats import ResourceDrained


class MockValue(SupportsGetValue):

    def __init__(self, _value: Decimal) -> None:
        self._value = _value

    def get_value(self) -> Decimal:
        return self._value

    @property
    def value(self) -> Decimal:
        return self.get_value()

    @value.setter
    def value(self, new_value: Decimal) -> None:
        self._value = new_value


class TestDynamicValue:

    @pytest.fixture
    def mock_source(self) -> MockValue:
        return MockValue(Decimal(10))

    def test_value_changes_if_source_value_changes(self, mock_source: MockValue) -> None:
        dynamic_value = DynamicValue(mock_source)

        before = dynamic_value.get_value()
        mock_source.value += 1
        after = dynamic_value.get_value()

        assert before != after

    def test_value_stays_decimal_if_float_multiplier_is_given_in_constructor(self, mock_source: MockValue) -> None:
        dynamic_value = DynamicValue(mock_source, 11.11)
        assert isinstance(dynamic_value.get_value(), Decimal)


class TestConstValue:

    def test_instances_from_equal_decimals_are_same(self) -> None:
        first = ConstValue(Decimal('12.34'))
        second = ConstValue(Decimal('12.34'))

        assert first is second

    def test_instances_from_equal_floats_are_same(self) -> None:
        first = ConstValue(12.34)
        second = ConstValue(12.34)

        assert first is second

    def test_instances_from_equal_int_and_decimal_are_same(self) -> None:
        from_int = ConstValue(10)
        from_decimal = ConstValue(Decimal(10))

        assert from_int is from_decimal

    def test_instances_with_unequal_values_are_not_same(self) -> None:
        first = ConstValue(Decimal(1))
        second = ConstValue(Decimal(2))

        assert first is not second


class TestModifier:

    @pytest.fixture
    def base_value(self) -> MockValue:
        return MockValue(Decimal(10))

    @pytest.mark.parametrize('base_arguments_of_value_ten', (lazy_fixture('base_value'), 10, 10.0, '10', '10.0', Decimal('10.0'), DecimalTuple(0, (1, 0, 0), -1)))
    def test_decimal_bases_return_proper_value(self, base_arguments_of_value_ten: Any) -> None:
        assert Modifier(base_arguments_of_value_ten,
                        Modification.FLAT).get_value() == Decimal(10)

    def test_value_base_returns_proper_value(self, base_value: MockValue) -> None:
        assert Modifier(
            base_value, Modification.FLAT).get_value() == Decimal(10)

    # def test_value_is_read_only(self) -> None:
    #     modifier = Modifier(1, Modification.FLAT)
    #     with pytest.raises(AttributeError):
    #         modifier.value += 1  # type: ignore [misc]

    def test_value_changes_if_base_value_changes(self, base_value: MockValue) -> None:
        modifier = Modifier(base_value, Modification.FLAT)

        before = modifier.get_value()
        base_value.value += 1
        after = modifier.get_value()

        assert before != after

    def test_flat_goes_before_percent_additive(self) -> None:
        flat_modifier = Modifier(1, Modification.FLAT)
        percent_additive_modifier = Modifier(1, Modification.PERCENT_ADDITIVE)

        assert flat_modifier.order < percent_additive_modifier.order

    def test_percent_additive_goes_before_percent_multiplicative(self) -> None:
        percent_additive_modifier = Modifier(1, Modification.PERCENT_ADDITIVE)
        percent_multiplicative_modifier = Modifier(
            1, Modification.PERCENT_MULTIPLICATIVE)

        assert percent_additive_modifier.order < percent_multiplicative_modifier.order


class TestStat:

    @pytest.fixture(scope="function", autouse=True)
    def hide_abstract_methods(self, mocker: MockFixture) -> None:
        mocker.patch('src.game.stats.Stat.__abstractmethods__', set())

    @pytest.fixture
    def vitality(self) -> Stat:
        # Abstract methods have been hidden via 'hide_abstract_methods' fixture.
        return Stat(Decimal(10))    # type: ignore [abstract]

    @pytest.fixture
    def buff_flat(self) -> Modifier:
        return Modifier(1, Modification.FLAT)

    @pytest.fixture
    def buff_percent_add(self) -> Modifier:
        return Modifier(0.5, Modification.PERCENT_ADDITIVE)

    @pytest.fixture
    def buff_percent_mult(self) -> Modifier:
        return Modifier(0.5, Modification.PERCENT_MULTIPLICATIVE)

    @pytest.fixture
    def modifiers(self, buff_flat: Modifier, buff_percent_add: Modifier, buff_percent_mult: Modifier) -> list[Modifier]:
        return [buff_flat, buff_percent_add, buff_percent_mult]

    @pytest.mark.parametrize('modifier', (lazy_fixture('buff_flat'), lazy_fixture('buff_percent_add'), lazy_fixture('buff_percent_mult')))
    def test_added_modifiers_are_in_modifiers(self, vitality: Stat, modifier: Modifier) -> None:
        vitality.add_modifier(modifier)
        assert modifier in vitality.modifiers

    def test_adding_modifiers_sorts_modifiers_by_order(self, vitality: Stat, buff_flat: Modifier, buff_percent_add: Modifier) -> None:
        vitality.add_modifier(buff_percent_add)
        vitality.add_modifier(buff_flat)
        assert next(m for m in vitality.modifiers) is buff_flat

    def test_adding_flat_modifier_adds_its_value(self, vitality: Stat, buff_flat: Modifier) -> None:
        expected = vitality.get_value() + buff_flat.get_value()
        vitality.add_modifier(buff_flat)
        actual = vitality.get_value()

        assert expected == actual

    def test_adding_percent_multiplicative_modifier_multiplies_by_its_value(self, vitality: Stat, buff_percent_mult: Modifier) -> None:
        expected = vitality.get_value() * (Decimal(1) + buff_percent_mult.get_value())
        vitality.add_modifier(buff_percent_mult)
        actual = vitality.get_value()

        assert expected == actual

    def test_adding_percent_additive_modifiers_multiplies_by_sum_of_their_values(self, vitality: Stat, buff_percent_add: Modifier) -> None:
        expected = vitality.get_value() * \
            (Decimal(1) + buff_percent_add.get_value() + buff_percent_add.get_value())
        vitality.add_modifier(buff_percent_add)
        vitality.add_modifier(buff_percent_add)
        actual = vitality.get_value()

        assert expected == actual

    def test_value_changes_if_modifier_value_changes(self, vitality: Stat, mocker: MockFixture) -> None:
        modifier = Modifier(Decimal(1), Modification.FLAT)
        vitality.add_modifier(modifier)

        before = vitality.get_value()
        mocker.patch('src.game.stats.Modifier.get_value', return_value=5)
        after = vitality.get_value()

        assert after - before == Decimal(4)

    def test_modifier_does_not_affect_base_value(self, vitality: Stat, buff_flat: Modifier) -> None:
        before = vitality.base
        vitality.add_modifier(buff_flat)
        after = vitality.base

        assert before == after

    def test_removing_modifier_removes_its_effect(self, vitality: Stat, buff_flat: Modifier) -> None:
        before = vitality.base
        vitality.add_modifier(buff_flat)
        vitality.remove_modifier(buff_flat)
        after = vitality.base

        assert before == after

    def test_removing_source_removes_all_modifiers_from_it(self, vitality: Stat) -> None:
        curse = Modifier(-1, Modification.FLAT, _source="necromancer")
        disease = Modifier(-0.5, Modification.PERCENT_MULTIPLICATIVE,
                           _source="necromancer")

        before = vitality.get_value()
        vitality.add_modifier(curse)
        vitality.add_modifier(disease)
        vitality.remove_source("necromancer")
        after = vitality.get_value()

        assert before == after

    def test_modifiers_are_applied_in_order(self, vitality: Stat) -> None:
        first = Modifier(1, Modification.FLAT, _order=1)
        second = Modifier(0.3, Modification.PERCENT_MULTIPLICATIVE, _order=2)
        third = Modifier(3, Modification.FLAT, _order=3)
        fourth = Modifier(0.2, Modification.PERCENT_ADDITIVE, _order=4)
        fifth = Modifier(0.1, Modification.PERCENT_ADDITIVE, _order=4)
        sixth = Modifier(-0.5, Modification.PERCENT_MULTIPLICATIVE, _order=5)

        vitality.add_modifier(sixth)
        vitality.add_modifier(fourth)
        vitality.add_modifier(fifth)
        vitality.add_modifier(second)
        vitality.add_modifier(third)
        vitality.add_modifier(first)

        expected = vitality.base
        expected += first.get_value()
        expected *= (1 + second.get_value())
        expected += third.get_value()
        expected *= (1 + fourth.get_value() + fifth.get_value())
        expected *= (1 + sixth.get_value())

        actual = vitality.get_value()

        assert expected == actual

    def test_temporary_modifiers_do_not_persist(self, vitality: Stat, modifiers: list[Modifier]) -> None:
        _ = vitality.get_value(modifiers)
        assert not vitality.modifiers

    def test_temporary_modifiers_do_not_change_value(self, vitality: Stat, modifiers: list[Modifier]) -> None:
        before = vitality.get_value()
        _ = vitality.get_value(modifiers)
        after = vitality.get_value()

        assert before == after

    def test_temporary_flat_modifier_adds_its_value(self, vitality: Stat, buff_flat: Modifier) -> None:
        expected = vitality.get_value() + buff_flat.get_value()
        actual = vitality.get_value([buff_flat])

        assert expected == actual

    def test_temporary_percent_multiplicative_modifier_multiplies_by_its_value(self, vitality: Stat, buff_percent_mult: Modifier) -> None:
        expected = vitality.get_value() * (Decimal(1) + buff_percent_mult.get_value())
        actual = vitality.get_value(
            [buff_percent_mult])

        assert expected == actual

    def test_temporary_percent_additive_modifiers_multiply_by_sum_of_their_values(self, vitality: Stat, buff_percent_add: Modifier) -> None:
        expected = vitality.get_value() * \
            (Decimal(1) + buff_percent_add.get_value() + buff_percent_add.get_value())
        actual = vitality.get_value(
            [buff_percent_add, buff_percent_add])

        assert expected == actual

    def test_temporary_modifiers_are_applied_in_order(self, vitality: Stat) -> None:
        first = Modifier(1, Modification.FLAT, _order=1)
        second = Modifier(0.3, Modification.PERCENT_MULTIPLICATIVE, _order=2)
        third = Modifier(3, Modification.FLAT, _order=3)
        fourth = Modifier(0.2, Modification.PERCENT_ADDITIVE, _order=4)
        fifth = Modifier(0.1, Modification.PERCENT_ADDITIVE, _order=4)
        sixth = Modifier(-0.5, Modification.PERCENT_MULTIPLICATIVE, _order=5)

        expected = vitality.base
        expected += first.get_value()
        expected *= (1 + second.get_value())
        expected += third.get_value()
        expected *= (1 + fourth.get_value() + fifth.get_value())
        expected *= (1 + sixth.get_value())

        actual = vitality.get_value(
            [sixth, fourth, fifth, second, third, first])

        assert expected == actual

    def test_temporary_modifiers_are_applied_in_order_with_persistent_modifiers(self, vitality: Stat) -> None:
        first = Modifier(1, Modification.FLAT, _order=1)
        second = Modifier(0.3, Modification.PERCENT_MULTIPLICATIVE, _order=2)
        third = Modifier(3, Modification.FLAT, _order=3)
        fourth = Modifier(0.2, Modification.PERCENT_ADDITIVE, _order=4)
        fifth = Modifier(0.1, Modification.PERCENT_ADDITIVE, _order=4)
        sixth = Modifier(-0.5, Modification.PERCENT_MULTIPLICATIVE, _order=5)

        vitality.add_modifier(sixth)
        vitality.add_modifier(first)
        vitality.add_modifier(fourth)

        expected = vitality.base
        expected += first.get_value()
        expected *= (1 + second.get_value())
        expected += third.get_value()
        expected *= (1 + fourth.get_value() + fifth.get_value())
        expected *= (1 + sixth.get_value())

        actual = vitality.get_value(
            [fifth, second, third])

        assert expected == actual

    def test_temporary_modifiers_do_not_remove_effects_of_persistent_modifiers(self, vitality: Stat) -> None:
        vitality.add_modifier(Modifier(Decimal(1), Modification.FLAT))
        before = vitality.get_value()
        _ = vitality.get_value(
            [Modifier(Decimal('0.5'), Modification.PERCENT_MULTIPLICATIVE)])
        after = vitality.get_value()

        assert before == after

    def test_temporary_modifiers_do_not_remove_persistent_modifiers(self, vitality: Stat) -> None:
        persistent = Modifier(Decimal(1), Modification.FLAT)
        vitality.add_modifier(persistent)
        _ = vitality.get_value(
            [Modifier(Decimal('0.5'), Modification.PERCENT_MULTIPLICATIVE)])

        assert persistent in vitality.modifiers


class TestBoundedStat:

    @pytest.mark.parametrize('invalid_base', (-1, 101))
    def test_passing_base_out_of_bounds_raises_value_error(self, invalid_base: int) -> None:
        with pytest.raises(ValueError):
            _ = BoundedStat(invalid_base, 0, 100, 125)

    def test_passing_modified_upper_bound_value_when_upper_bound_is_none_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            _ = BoundedStat(1, None, None, 125)

    def test_passing_modified_upper_bound_less_than_upper_bound_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            _ = BoundedStat(1, 0, 100, 75)

    @pytest.mark.parametrize('modifier_value', (-200, 200))
    def test_modifiers_cannot_push_value_out_of_bounds(self, modifier_value: int) -> None:
        vitality = BoundedStat(1, 0, 100, 125)
        vitality.add_modifier(Modifier(modifier_value, Modification.FLAT))

        assert 0 <= vitality.get_value() <= 125

    @pytest.mark.parametrize('new_base', (-200, 200))
    def test_cannot_push_base_out_of_bounds(self, new_base: int) -> None:
        vitality = BoundedStat(1, 0, 100, 125)
        vitality.base += new_base

        assert 0 <= vitality.base <= 100

    def test_capped_is_true_when_base_equals_upper_bound(self) -> None:
        vitality = BoundedStat(100, 0, 100, 125)
        assert vitality.is_capped()

    def test_capped_is_false_when_base_is_below_upper_bound(self) -> None:
        vitality = BoundedStat(99, 0, 100, 125)
        assert not vitality.is_capped()

    def test_modifying_current_value_does_not_change_is_capped_return_value(self) -> None:
        vitality = BoundedStat(99, 0, 100, 125)
        vitality.add_modifier(Modifier(100, Modification.FLAT))
        assert not vitality.is_capped()

    @pytest.mark.parametrize('modifier_value', (Decimal(-200), Decimal(200)))
    def test_temporary_modifiers_cannot_push_value_out_of_bounds(self, modifier_value: Decimal) -> None:
        vitality = BoundedStat(1, 0, 100, 125)
        temporary_value = vitality.get_value(
            [Modifier(modifier_value, Modification.FLAT)])

        assert 0 <= temporary_value <= 125


class TestResist:

    def test_base_becomes_passed_base_if_base_max_is_not_passed(self) -> None:
        physical = Resist(_base=1)
        assert physical.base == 1

    def test_base_increases_on_grow(self) -> None:
        physical = Resist(_base=1, _growth=1, _growth_max=1)
        expected = physical.base + physical.grow()
        actual = physical.base

        assert expected == actual

    # @pytest.mark.parametrize('growth_value', (Decimal(-200), Decimal(200)))
    # def test_grow_cannot_push_base_out_of_bounds(self, growth_value: Decimal) -> None:
    #     # In case Resist class will be changed.
    #     physical = Resist(_base=1, _growth=growth_value,
    #                       _growth_max=growth_value)
    #     physical._upper_bound = Decimal(100)
    #     physical.grow()

    #     assert 0 <= physical.base <= 100

    def test_passing_negative_growth_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            _ = Resist(_base=1, _growth=Decimal('-0.01'))

    def test_passing_negative_growth_max_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            _ = Resist(_base=1, _growth_max=Decimal('-0.01'))

    def test_passing_growths_equal_to_zero_does_not_raise_errors(self) -> None:
        _ = Resist(_base=1, _growth=Decimal(0), _growth_max=Decimal(0))


class TestCarryingCapacity:

    @pytest.mark.parametrize('load, expected_status', [
        (Decimal(100.00), LoadStatus.RED),
        (Decimal('100.01'), LoadStatus.RED),
        (Decimal('99.99'), LoadStatus.YELLOW),
        (Decimal('80.00'), LoadStatus.YELLOW),
        (Decimal('79.99'), LoadStatus.GREEN),
        (Decimal('60.00'), LoadStatus.GREEN),
        (Decimal('59.99'), LoadStatus.BLUE),
        (Decimal('40.00'), LoadStatus.BLUE),
        (Decimal('39.99'), LoadStatus.WHITE),
        (Decimal('00.00'), LoadStatus.WHITE)
    ])
    def test_load_status_fits_predefined_values(self, load: Decimal, expected_status: LoadStatus) -> None:
        capacity = CarryingCapacity(Decimal(100))
        capacity.load = load

        assert capacity.load_status is expected_status

    def test_load_cannot_go_below_zero(self) -> None:
        capacity = CarryingCapacity(Decimal(20))
        capacity.load -= Decimal(100)

        assert capacity.load == Decimal(0)


class TestResource:

    @pytest.fixture
    def hp(self) -> Resource:
        return Resource(10)

    def test_current_equals_total_after_construction(self, hp: Resource) -> None:
        assert hp.current == hp.get_value()

    @pytest.mark.parametrize('increment', (5, -5))
    def test_current_can_be_changed(self, hp: Resource, increment: int) -> None:
        expected = hp.current + increment
        hp.base = Decimal(20)
        hp.current += increment
        actual = hp.current

        assert expected == actual

    def test_current_cannot_be_increased_above_total(self, hp: Resource) -> None:
        hp.current += 20

        assert hp.current == hp.get_value()

    def test_current_can_be_increased_when_total_is_increased(self, hp: Resource) -> None:
        expected = hp.current + 10
        hp.base += 20
        hp.current += 10
        actual = hp.current

        assert expected == actual

    def test_current_can_be_increased_when_total_is_increased_with_modifiers(self, hp: Resource) -> None:
        expected = hp.current + 10
        hp.add_modifier(Modifier(20, Modification.FLAT))
        hp.current += 10
        actual = hp.current

        assert expected == actual

    def test_current_cannot_be_decreased_below_lower_bound(self) -> None:
        sp = Resource(_base=10, _lower_bound=0)

        # with suppress(ResourceDrained):
        #     sp.current -= 20
        sp.current -= 20

        assert sp.current == 0

    def test_decreasing_total_below_current_changes_current(self, hp: Resource) -> None:
        expected = hp.current - 5
        hp.base -= 5
        actual = hp.current

        assert expected == actual

    def test_changing_total_above_current_does_not_change_current(self, hp: Resource) -> None:
        expected = hp.current
        hp.base += Decimal('20.00')
        hp.base -= Decimal('19.99')
        actual = hp.current

        assert expected == actual

    def test_modifiers_decreasing_total_below_current_change_current(self, hp: Resource) -> None:
        debuff = Modifier(-1, Modification.FLAT)
        expected = hp.current - 1
        hp.add_modifier(debuff)
        actual = hp.current

        assert expected == actual

    def test_modifiers_changing_total_above_current_do_not_change_current(self, hp: Resource) -> None:
        expected = hp.current
        hp.add_modifier(Modifier(10, Modification.FLAT))
        hp.add_modifier(Modifier(0.3, Modification.PERCENT_MULTIPLICATIVE))
        hp.add_modifier(Modifier(-9, Modification.FLAT))
        actual = hp.current

        assert expected == actual

    def test_removing_positive_modifier_changes_current_if_total_becomes_less_than_current(self, hp: Resource) -> None:
        expected = hp.current
        buff = Modifier(10, Modification.FLAT)
        hp.add_modifier(buff)
        hp.current += 5
        hp.remove_modifier(buff)
        actual = hp.current

        assert expected == actual

    def test_change_of_modifier_source_affects_current(self, hp: Resource) -> None:
        source = MockValue(Decimal(10))
        buff = Modifier(source, Modification.FLAT)
        hp.add_modifier(buff)

        expected = hp.current + 1
        hp.current += 5
        source.value = Decimal(1)
        actual = hp.current

        assert expected == actual

    # def test_constructing_with_base_equal_to_zero_does_not_raise_resource_drained(self) -> None:
    #     _ = Resource(Decimal(0))

    # @pytest.mark.parametrize('decrement', (10, 11, 100, Decimal('10.01')))
    # def test_reducing_current_to_zero_raises_resource_drained(self, hp: Resource, decrement: Decimal | int) -> None:
    #     with pytest.raises(ResourceDrained):
    #         hp.current -= decrement

    # @pytest.mark.parametrize('decrement', (1, Decimal('1.99')))
    # def test_reducing_current_to_above_zero_does_not_raise(self, decrement: Decimal | int) -> None:
    #     mp = Resource(Decimal(2))
    #     mp.current -= decrement

    # def test_reducing_current_from_zero_to_zero_does_not_raise(self, hp: Resource) -> None:
    #     with pytest.raises(ResourceDrained):
    #         hp.current -= 10

    #     hp.current -= 1  # Should not raise since current is already 0.

    # def test_increasing_drained_current_resets_drained_status(self, hp: Resource) -> None:
    #     with pytest.raises(ResourceDrained):
    #         hp.current -= 10

    #     hp.current += 1

    #     with pytest.raises(ResourceDrained):
    #         hp.current -= 1

    # def test_regenerating_zero_does_not_reset_drained_status(self) -> None:
    #     sp = Resource(_base=1, _regeneration=0)

    #     with pytest.raises(ResourceDrained):
    #         sp.current -= 1

    #     sp.regenerate()
    #     sp.current -= 1

    # @pytest.mark.parametrize('decrement', (10, 100, Decimal('10.01')))
    # def test_reducing_base_which_results_in_reducing_current_to_zero_raises_resource_drained(self, hp: Resource, decrement: Decimal | int) -> None:
    #     with pytest.raises(ResourceDrained):
    #         hp.base -= decrement

    # @pytest.mark.parametrize('decrement', (1, Decimal('1.99')))
    # def test_reducing_base_which_results_in_reducing_current_to_above_zero_does_not_raise(self, decrement: Decimal | int) -> None:
    #     mp = Resource(Decimal(2))
    #     mp.base -= decrement

    # def test_adding_modifiers_which_results_in_reducing_current_to_zero_raises_resource_drained(self, hp: Resource) -> None:
    #     with pytest.raises(ResourceDrained):
    #         hp.add_modifier(Modifier(-10, Modification.FLAT))

    # def test_removing_modifiers_which_results_in_reducing_current_to_zero_raises_resource_drained(self) -> None:
    #     mp = Resource(0)
    #     buff = Modifier(1, Modification.FLAT)
    #     mp.add_modifier(buff)
    #     mp.current += 1

    #     with pytest.raises(ResourceDrained):
    #         mp.remove_modifier(buff)

    # def test_changing_modifier_source_which_results_in_reducing_current_to_zero_raises_resource_drained(self) -> None:
    #     source = MockValue(Decimal(1))
    #     modifier = Modifier(source, Modification.FLAT)
    #     mp = Resource(0)
    #     mp.add_modifier(modifier)
    #     mp.current += 1

    #     with pytest.raises(ResourceDrained):
    #         source.value = 0


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
