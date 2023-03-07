"""Representation of config APIs."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping

if TYPE_CHECKING:
    from .widget import Widget


class Blueprint(Mapping[str, object]):

    ...


class WidgetTrigger(Blueprint):

    def onKill(self, widget: 'Widget') -> None: ...
    def onSend(self, widget: 'Widget', data_sent: Any) -> None: ...
    def onUse(self, widget: 'Widget') -> None: ...


class WidgetBlueprint(Blueprint):

    texture: TextureBlueprint
    trigger: WidgetTrigger



class TextboxBlueprint(WidgetBlueprint):

    text: str
    font: FontBlueprint
    editable: bool
    killable: bool


class ImageboxBlueprint(WidgetBlueprint):

    image: AtlasBlueprint


class SignedImageBlueprint(WidgetBlueprint):

    image: AtlasBlueprint
    text: str
    font: FontBlueprint
    width_spacing: int


class FontBlueprint(Blueprint):

    name: str
    size: float
    color: str


class AtlasBlueprint(Blueprint):

    source: str
    alpha: bool


class TextureBlueprint(Blueprint):

    size: Size
    part_size: Size
    source: str
    alpha: bool
    parts: Mapping[str, int]


class Size(Blueprint):

    x: int
    y: int


def size_to_tuple(size: Size) -> tuple[int, int]:
    return (size.x, size.y)
