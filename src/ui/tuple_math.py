
from typing import Any, Iterable, TypeVar

TIter = TypeVar("TIter", bound=Iterable[Any])


def add(first: TIter, second: TIter) -> TIter:
    return type(first)(x+y for x, y in zip(first, second))


def sub(first: TIter, second: TIter) -> TIter:
    return type(first)(x-y for x, y in zip(first, second))


def div(first: TIter, second: TIter) -> TIter:
    return type(first)(x / y for x, y in zip(first, second))


def mult(first: TIter, second: TIter) -> TIter:
    return type(first)(x * y for x, y in zip(first, second))


def less(first: TIter, second: TIter) -> bool:
    return all(x < y for x, y in zip(first, second))


def less_or_equal(first: TIter, second: TIter) -> bool:
    return all(x <= y for x, y in zip(first, second))
