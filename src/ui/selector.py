from __future__ import annotations

from typing import ClassVar, Iterable, assert_never

import pygame as pg
from pygame import Surface
from pygame.event import Event
from pygame.freetype import Font
from pygame.sprite import OrderedUpdates
from typing_extensions import override

# TODO:
# import keybind, shared, tuple_math
# from shared import Direction, pair
from src import keybind, shared, tuple_math
from src.shared import Direction, pair

from .dialogue import DialogueSprite
from .observer import ListEvent, ListEventType, ListPublisher, Subscriber
from .textbox import create_default_font
from .widget import Widget, WidgetSprite, WidgetTrigger


class Selector(Widget):

    def __init__(self,
                 data_source: ListPublisher[Selection],
                 bg: Surface,
                 trigger: WidgetTrigger,
                 padding: tuple[int, int, int, int],
                 columns: int = 1,
                 spacing: pair[int] = (4, 4),
                 font: Font | None = None,
                 selection_size: pair[int] = (0, 0),
                 closeable: bool = True,
                 ) -> None:

        super().__init__(bg, trigger)

        self._data_source = data_source
        self._closeable = closeable

        surf_size = shared.calculate_subsurface_size(bg, padding)
        self._selection_sprite = SelectionSprite(surf_size,
                                                 data_source,
                                                 font,
                                                 columns,
                                                 spacing,
                                                 selection_size)
        self._selection_sprite.set_offset_base(padding[:2])
        self._sprites.add(self._selection_sprite)
        data_source.add_subscriber(self._selection_sprite)

        self._scroll_mode = True

    @override
    def handle_inputs(self) -> None:
        super().handle_inputs()

        for event in pg.event.get(eventtype=(pg.KEYDOWN)):
            self._handle_in_scroll_mode(
                event) if self._scroll_mode else self._handle_in_select_mode(event)

    def get_selected(self) -> Selection:
        return self._selection_sprite.get_selected()

    def _handle_in_scroll_mode(self, event: Event) -> None:
        assert self._scroll_mode

        if (key := event.key) in keybind.ESCAPE:
            self.kill()
            return
        elif key in keybind.USE:
            self._scroll_mode = False
            self._trigger.onUse(self)
        elif key in keybind.SEND:
            self._trigger.onSend(self, self.get_selected().item)
        elif (direction := keybind.key_to_direction(key)) is not None:
            self._selection_sprite.scroll_selection(direction)

    def _handle_in_select_mode(self, event: Event) -> None:
        assert not self._scroll_mode

        if (key := event.key) in keybind.ESCAPE:
            self._scroll_mode = True
        elif (direction := keybind.key_to_direction(key)) is not None:
            self._selection_sprite.get_selected_sprite().scroll(direction)


class SelectionSprite(WidgetSprite, Subscriber):

    _scroll_step: pair[int]

    def __init__(self,
                 size: pair[int],
                 data_source: ListPublisher[Selection],
                 font: Font | None = None,
                 columns: int = 1,
                 spacing: pair[int] = (4, 4),
                 selection_size: pair[int] = (0, 0),
                 ) -> None:

        image = shared.build_transparent_surface(size)
        super().__init__(image)
        self._data_source = data_source
        data_source.add_subscriber(self)
        self._columns = columns
        self._font = font if font is not None else create_default_font()
        self._font.origin = True

        assert isinstance(self._font.size, float)
        self._font_size_base = self._font.size
        self._display_position = (0, 0)
        self._selected_index = 0
        self._wrapper = SelectionWrapper(columns, spacing, self._font)
        self._selection_size_base = selection_size

        # TODO: Choose a method to set the scroll step up.
        self._scroll_step = (10, 10)
        self._sprites = OrderedUpdates(self._data_wrap(data_source))
        self.get_selected_sprite().highlight()

    @override
    def notify(self, event: ListEvent[Selection]) -> None:
        if (eventtype := event.eventtype) is ListEventType.SETITEM:
            self._handle_setitem(event)
        elif eventtype is ListEventType.DELITEM:
            self._handle_delitem(event)
        elif eventtype is ListEventType.APPEND:
            self._handle_append(event)
        elif eventtype is ListEventType.REMOVE:
            self._handle_remove(event)
        elif eventtype is ListEventType.CLEAR:
            self._handle_clear(event)
        elif eventtype is ListEventType.EXTEND:
            self._handle_extend(event)
        elif eventtype is ListEventType.INSERT:
            self._handle_insert(event)
        else:
            assert_never(eventtype)

    @override
    def scale(self, factor: pair[float]) -> None:
        super().scale(factor)
        self._font.size = self._font_size_base * factor[1]

    @override
    def update(self, dt: float) -> None:
        super().update(dt)

        #
        # self._sprites = self._data_wrap(self._data_source)
        # for sprite in self._sprites:
        # sprite.set_offset_base(tuple_math.sub(sprite._offset_base,
        #                                       self._display_position))
        # self.get_selected_sprite().highlight()

    @override
    def _reposition_sprites(self) -> None:
        display_position = tuple_math.mult(self._display_position,
                                           self._scale_factor)
        center = tuple_math.sub(self.rect.center,
                                display_position)

        for sprite in self._sprites:
            if sprite.centered:
                sprite.center_at(tuple_math.intify(center))
            else:
                sprite.position_at(tuple_math.intify(
                    tuple_math.sub(sprite.calculate_offset(),
                                   display_position)))

    def can_scroll(self, direction: Direction) -> bool:
        x, y = self._display_position

        if direction is Direction.UP:
            return y > 0
        elif direction is Direction.LEFT:
            return x > 0
        elif direction is Direction.DOWN:
            last_sprite = list(self._sprites)[-1]
            return not self.reaches_side(last_sprite, Direction.DOWN)
        elif direction is Direction.RIGHT:
            try:
                rightmost_sprite = (sprites := list(self._sprites))[
                    self._columns-1]
            except IndexError:
                rightmost_sprite = sprites[-1]
            return not self.reaches_side(rightmost_sprite, Direction.RIGHT)

        return False

    def get_selected(self) -> Selection:
        return self._data_source[self._selected_index]

    def get_selected_sprite(self) -> DialogueSprite:
        return list(self._sprites)[self._selected_index]

    def scroll(self, direction: Direction) -> None:
        x, y = self._display_position
        step_x, step_y = self._scroll_step

        if direction is Direction.UP:
            y -= step_y
        elif direction is Direction.LEFT:
            x -= step_x
        elif direction is Direction.DOWN:
            y += step_y
        elif direction is Direction.RIGHT:
            x += step_x
        else:
            return

        self._display_position = (x, y)
        self._adjust_position()

    def scroll_selection(self, direction: Direction) -> None:
        index = self._selected_index
        columns = self._columns

        if direction is Direction.UP and index >= columns:
            index -= columns
        elif direction is Direction.LEFT and index % columns > 0:
            index -= 1
        elif direction is Direction.DOWN and index + columns < len(self._sprites):
            index += columns
        elif all((direction is Direction.RIGHT,
                  index % columns < columns - 1,
                  index < len(self._sprites) - 1)):
            index += 1
        else:
            return

        self.get_selected_sprite().highlight(False)
        self._selected_index = index
        self.get_selected_sprite().highlight(True)

        while not self.reaches_side(self.get_selected_sprite(), direction) and self.can_scroll(direction):
            self.scroll(direction)

    def reaches_side(self, sprite: WidgetSprite, side: Direction) -> bool:
        x, y = tuple_math.intify(tuple_math.mult((self._display_position),
                                                 (self._scale_factor)))
        offset_x, offset_y = sprite.calculate_offset()

        if side is Direction.UP:
            # return self.rect.top + y <= sprite.rect.top
            return offset_y >= y
        elif side is Direction.LEFT:
            # return self.rect.left + x <= sprite.rect.left
            return offset_x >= x
        elif side is Direction.DOWN:
            return offset_y + sprite.rect.height <= y + self.rect.height
            # return self.rect.bottom + y >= sprite.rect.bottom
        elif side is Direction.RIGHT:
            return offset_x + sprite.rect.width <= x + self.rect.width
            # return self.rect.right + x >= sprite.rect.right
        else:
            raise ValueError(f"Cannot determine side collision for {side}.")

    def _adjust_position(self) -> None:
        last_child = list(self._sprites)[-1]
        # NOTE: You probably want to subtract self.rect.size.
        max_x, max_y = tuple_math.add(last_child.calculate_offset(),
                                      last_child.rect.size)
        x, y = self._display_position

        x = int(max(0, min(x, max_x)))
        y = int(max(0, min(y, max_y)))

        self._display_position = (x, y)

    def update_scroll_step(self) -> None:
        self._scroll_step = (10, 10)

    def _handle_setitem(self, event: ListEvent[Selection]) -> None:
        assert event.eventtype is ListEventType.SETITEM

        if not isinstance((key := event.key), slice):
            key = slice(key, key+1, 1)

        if not isinstance((value := event.value), Iterable):
            value = (value,)

        sprites = list(self._sprites)
        new_sprites = self._data_wrap(value)
        sprites[key] = new_sprites

        self._sprites.empty()
        self._sprites.add(sprites)

    def _handle_delitem(self, event: ListEvent[Selection]) -> None:
        assert event.eventtype is ListEventType.DELITEM

        sprites = list(self._sprites)
        del sprites[event.key]

        self._sprites.empty()
        self._sprites.add(sprites)

    def _handle_append(self, event: ListEvent[Selection]) -> None:
        assert event.eventtype is ListEventType.APPEND

        if not isinstance((value := event.value), Iterable):
            value = (value,)

        new_sprites = self._data_wrap(value)
        self._sprites.add(new_sprites)

    def _handle_remove(self, event: ListEvent[Selection]) -> None:
        assert event.eventtype is ListEventType.REMOVE

        value = event.value

        sprites = [
            sprite for sprite in self._sprites if not sprite.selection is value]

        self._sprites.empty()
        self._sprites.add(sprites)

    def _handle_clear(self, event: ListEvent[Selection]) -> None:
        assert event.eventtype is ListEventType.CLEAR

        self._sprites.empty()

    def _handle_extend(self, event: ListEvent[Selection]) -> None:
        assert event.eventtype is ListEventType.EXTEND

        assert isinstance(event.value, Iterable)
        new_sprites = self._data_wrap(event.value)
        self._sprites.add(new_sprites)

    def _handle_insert(self, event: ListEvent[Selection]) -> None:
        assert event.eventtype is ListEventType.INSERT

        sprites = list(self._sprites)
        index = event.index

        assert not isinstance(event.value, Iterable)
        value = (event.value,)
        new_sprites = self._data_wrap(value)
        sprites.insert(index, new_sprites[0])

    def _data_wrap(self, data_source: Iterable[Selection]) -> list[DialogueSprite]:
        selection_size = tuple_math.intify(tuple_math.mult(self._selection_size_base,
                                                           self._scale_factor))
        return self._wrapper.get_sprites(data_source, selection_size)


class Selection:

    image: Surface
    text: str
    header: str = ""
    item: object = None


class SelectionWrapper:

    TEXT_SPACING: ClassVar = 2
    DIALOGUE_SPACING: ClassVar = (4, 4)

    def __init__(self,
                 columns: int,
                 spacing: pair[int],
                 font: Font,
                 ) -> None:

        self._columns = columns
        self._spacing = spacing
        self._font = font

    def get_sprites(self, data_source: Iterable[Selection], base_selection_size: pair[int] = (0, 0)) -> list[DialogueSprite]:
        def clean(word: str) -> str:
            return word.rstrip("\n")

        def get_size(selection: Selection) -> pair[int]:
            text_area_width = max(self._font.get_rect(
                clean(word)).width for word in selection.text.split(" "))
            width = selection.image.get_width() + self.TEXT_SPACING + text_area_width
            height = selection.image.get_height()
            return (width, height)

        items = [(selection, get_size(selection)) for selection in data_source]
        max_size = tuple_math.max_(
            *(size for _, size in items), base_selection_size)
        sprites = []

        x, y = 0, 0
        column = 0

        for selection, _ in items:
            sprite = DialogueSprite(max_size,
                                    selection.image,
                                    selection.text,
                                    selection.header,
                                    self.DIALOGUE_SPACING,
                                    self._font)
            sprite.set_offset_base((x, y))
            x += max_size[0] + self._spacing[0]
            column += 1

            if column >= self._columns:
                x = 0
                y += max_size[1] + self._spacing[1]
                column = 0

            sprites.append(sprite)

        return sprites
