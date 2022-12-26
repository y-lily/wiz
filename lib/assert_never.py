from typing import NoReturn


def assert_never(value: NoReturn) -> NoReturn:
    assert False, f"Unexpected value {value} of type {type(value).__name__}"
