from decimal import Decimal, DecimalTuple
from typing import Any

import pytest
from pytest_lazyfixture import lazy_fixture

from src.game.stats.modifier import (
    ConstValue, DynamicValue, Modification, Modifier)
from tests.game.mock_value import MockValue


class TestDynamicValue:

    @pytest.fixture
    def mock_source(self) -> MockValue:
        return MockValue(Decimal(10))

    def test_value_changes_if_source_value_changes(self, mock_source: MockValue) -> None:
        dynamic_value = DynamicValue(mock_source)

        before = dynamic_value.value
        mock_source.value += 1
        after = dynamic_value.value

        assert before != after

    def test_value_stays_decimal_if_float_multiplier_is_given_in_constructor(self, mock_source: MockValue) -> None:
        dynamic_value = DynamicValue(mock_source, 11.11)
        assert isinstance(dynamic_value.value, Decimal)


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
                        Modification.FLAT).value == Decimal(10)

    def test_value_base_returns_proper_value(self, base_value: MockValue) -> None:
        assert Modifier(base_value, Modification.FLAT).value == Decimal(10)

    def test_value_is_read_only(self) -> None:
        modifier = Modifier(1, Modification.FLAT)
        with pytest.raises(AttributeError):
            modifier.value += 1  # type: ignore [misc]

    def test_value_changes_if_base_value_changes(self, base_value: MockValue) -> None:
        modifier = Modifier(base_value, Modification.FLAT)

        before = modifier.value
        base_value.value += 1
        after = modifier.value

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
