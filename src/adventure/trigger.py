from typing import Any, Callable, TypedDict


class Trigger(TypedDict):

    onEnter: Callable[..., Any]
    onExit: Callable[..., Any]
    onUse: Callable[..., Any]
