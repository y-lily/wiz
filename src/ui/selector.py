from __future__ import annotations

from dataclasses import dataclass

import pygame as pg
from pygame.surface import Surface
from typing_extensions import override

from . import keybind
from .blueprint import WidgetTrigger
from .shared import Direction, pair
from .signed_image import SignedImage
from .textbox import ScrollData, Scroller
from .widget import Widget


class Selector(Widget):

    _active_widget: SignedImage | None
    _render_data: list[_ItemRenderData]
    _selected_index: int
    _scroller: Scroller[_ItemRenderData]

    def __init__(self,
                 data_source: list[ItemRepresentation],
                 bg_texture: Surface,
                 trigger: WidgetTrigger,
                 cell_size: pair,
                 columns: int = 1,
                 border_size: pair = (0, 0),
                 spacing: pair = (4, 4),
                 killable: bool = True,
                 ) -> None:

        super().__init__(bg_texture, trigger)

        self._cell_size = cell_size
        self._columns = columns
        self._border_size = border_size
        self._spacing = spacing

        self.set_data(data_source)

        self._killable = killable

    @override
    def handle_inputs(self) -> None:
        events = pg.event.get(eventtype=pg.KEYDOWN)

        for event in events:
            key = event.key

            if key in keybind.ESCAPE:
                self.kill()
                return

            elif key in keybind.USE:
                self._swap_active_widget()
                self._trigger.onUse(self)

            elif key in keybind.SEND:
                self._trigger.onSend(self, self.get_selected())

            elif all([(direction := keybind.key_to_direction(key)) is not None,
                     self._active_widget is None]):
                self.scroll_selection(direction)
                if not self._scroller.is_visible(self.get_selected()):
                    self.scroll(direction)

        if self._active_widget is not None:
            for event in events:
                pg.event.post(event)
                self._active_widget.handle_inputs()

    def set_data(self, data_source: list[ItemRepresentation]) -> None:
        for widget in self._widgets:
            widget.kill()

        assert len(self._widgets) == 0

        self._selected_index = 0
        self._active_widget = None

        self._render_data = self._wrap_data(data_source)
        # TODO: Visible area should be the inner rect.
        self._scroller = Scroller(
            self._render_data, self._background.rect.size, self._cell_size)

        for item in self._render_data:
            self.add(item.image)

    def get_selected(self) -> _ItemRenderData:
        return self._render_data[self._selected_index]

    def scroll(self, direction: Direction) -> None:
        if not self._scroller.can_scroll(direction):
            return

        self._scroller.scroll(direction)

    def scroll_selection(self, direction: Direction) -> None:
        index = self._selected_index
        columns = self._columns

        if direction is Direction.UP and index >= columns:
            index -= columns
        elif direction is Direction.DOWN and index < len(self._render_data) - columns:
            index += columns
        elif direction is Direction.LEFT and (index % columns) > 0:
            index -= 1
        elif direction is Direction.RIGHT and (index % columns) < columns - 1:
            index += 1

        self._selected_index = index

    def _swap_active_widget(self) -> None:
        if self._active_widget is None:
            self._active_widget = self.get_selected().image
        else:
            self._active_widget = None

    def _wrap_data(self, data_source: list[ItemRepresentation]) -> list[_ItemRenderData]:
        with ItemWrapper(self._border_size, self._spacing, self._columns) as wrapper:

            def assign_data(representation: ItemRepresentation) -> _ItemRenderData:
                return wrapper.wrap(_ItemRenderData(representation.image, representation.item))

            wrapped = [assign_data(item) for item in data_source]

        return wrapped


class ItemWrapper:

    def __init__(self, border_size: pair, spacing: pair, columns: int = 1) -> None:
        self._wrapper = self._Wrapper(border_size, spacing, columns)

    def __enter__(self) -> ItemWrapper._Wrapper:
        self._wrapper.start()
        return self._wrapper

    def __exit__(self, *args: object, **kwargs: object) -> None:
        self._wrapper.stop()
        del self._wrapper

    class _Wrapper:

        def __init__(self, border_size: pair, spacing: pair, columns: int) -> None:
            self.border_size = border_size
            self.spacing = spacing
            self.columns = columns

        def start(self) -> None:
            self.x, self.y = self.border_size
            self.column = 0

        def stop(self) -> None:
            del self.x, self.y, self.column

        def wrap(self, item_data: _ItemRenderData) -> _ItemRenderData:
            spacing = self.spacing
            size = item_data.size

            item_data.offset = self.x, self.y

            self.x += size[0] + spacing[0]
            self.column += 1
            if self.column >= self.columns:
                self.x = self.border_size[0]
                self.y += size[1] + spacing[1]
                self.column = 0

            return item_data


@dataclass
class ItemRepresentation:

    image: SignedImage
    item: object


@dataclass
class _ItemRenderData(ScrollData):

    image: SignedImage
    item: object

    @property
    def offset(self) -> pair:
        return self.image.offset_base

    @offset.setter
    def offset(self, new_offset: pair) -> None:
        self.image.set_offset_base(new_offset)

    @property
    def size(self) -> pair:
        return self.image.get_size()
