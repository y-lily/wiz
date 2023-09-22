"""Representation of config APIs."""
from __future__ import annotations

from typing import TYPE_CHECKING, Mapping

from tuple_math import pair

if TYPE_CHECKING:
    from .widget import WidgetTrigger


class Blueprint(Mapping[str, object]):

    ...


class WidgetBlueprint(Blueprint):

    bg: PanelBlueprint
    trigger: WidgetTrigger


class TextboxBlueprint(WidgetBlueprint):

    text: str
    font: FontBlueprint
    editable: bool
    closeable: bool


class DialogueBlueprint(TextboxBlueprint):

    portrait: AtlasBlueprint
    header: str
    spacing: Size


class SelectorBlueprint(WidgetBlueprint):

    data: Mapping[str, SelectionBlueprint]
    columns: int
    spacing: Size
    font: FontBlueprint
    selection_size: Size
    closeable: bool


class SelectionBlueprint(Blueprint):

    image: AtlasBlueprint
    text: str
    header: str
    item: ItemBlueprint


class ItemBlueprint(Blueprint):

    # TODO
    identifier: int
    obj: object = None


class FontBlueprint(Blueprint):

    name: str
    size: int
    color: str


class AtlasBlueprint(Blueprint):

    source: str
    alpha: bool


class PanelBlueprint(Blueprint):

    size: Size
    part_size: Size
    source: str
    alpha: bool


class Size(Blueprint):

    x: int
    y: int


def size_to_tuple(size: Size) -> pair[int]:
    return (size.x, size.y)
