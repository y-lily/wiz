
import math
from itertools import zip_longest
from typing import Any, Iterable, TypeVar, overload

TIter = TypeVar("TIter", bound=Iterable[Any])


def add(*iterables: TIter) -> TIter:
    return type(iterables[0])(sum(x) for x in zip_longest(*iterables, fillvalue=0))


def sub(first: TIter, second: TIter) -> TIter:
    return type(first)(x-y for x, y in zip_longest(first, second))


def div(first: TIter, second: TIter) -> TIter:
    return type(first)(x / y for x, y in zip(first, second))


def floor_div(first: TIter, second: TIter) -> TIter:
    return type(first)(x // y for x, y in zip(first, second))


def mult(first: TIter, second: TIter) -> TIter:
    return type(first)(x * y for x, y in zip(first, second))


def mod(first: TIter, second: TIter) -> TIter:
    return type(first)(x % y for x, y in zip(first, second))


def mod_round_down(first: TIter, second: TIter) -> TIter:
    return type(first)(x - x % y for x, y in zip(first, second))


def less(first: TIter, second: TIter) -> bool:
    return all(x < y for x, y in zip(first, second))


def less_or_equal(first: TIter, second: TIter) -> bool:
    return all(x <= y for x, y in zip(first, second))


def max_(*iterables: TIter) -> TIter:
    return type(iterables[0])(max(x) for x in zip_longest(*iterables, fillvalue=-math.inf))


def min_(*iterables: TIter) -> TIter:
    return type(iterables[0])(min(x) for x in zip_longest(*iterables, fillvalue=math.inf))


def neg(operand: TIter) -> TIter:
    return type(operand)(-x for x in operand)


@overload
def intify(operand: tuple[float, float]) -> tuple[int, int]:
    ...


@overload
def intify(operand: tuple[float, float, float]) -> tuple[int, int, int]:
    ...

# @overload
# def intify(operand: tuple[float, ...]) -> tuple[int, ...]:
    # ...


def intify(operand: tuple[float, ...]) -> tuple[int, ...]:
    return tuple(int(x) for x in operand)
