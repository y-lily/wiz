from __future__ import annotations

import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Generic, Protocol, TypeVar

import pygame as pg
import pygame.freetype
from pygame.event import Event
from pygame.freetype import Font, SysFont
from pygame.rect import Rect
from pygame.surface import Surface
from typing_extensions import override

from . import keybind, shared, tuple_math
from .blueprint import WidgetTrigger
from .shared import Direction, pair
from .widget import Widget, WidgetSprite


class Textbox(Widget):

    def __init__(self,
                 text: str,
                 bg_texture: Surface,
                 trigger: WidgetTrigger,
                 text_area_size: pair,
                 font: Font | None = None,
                 editable: bool = False,
                 killable: bool = True,
                 ) -> None:

        super().__init__(bg_texture, trigger)
        self._text = text
        self._editable = editable
        self._killable = killable

        text_surface = shared.build_transparent_surface(text_area_size)
        self._text_sprite = TextSprite(text_surface, text, font)
        self._text_sprite.centered = True
        self._spritegroup.add(self._text_sprite)

    def set_text(self, new_text: str) -> None:
        self._text = new_text
        self._text_sprite.set_text(new_text)

    def handle_inputs(self) -> None:
        # Delegate input handling to the top child if it is present and wants input.
        super().handle_inputs()

        # If the event queue is not empty after the delegation attempt, the widget
        # is free to handle inputs on its own.
        for event in pg.event.get(eventtype=(pg.KEYDOWN)):
            self._handle_keydown_event(event)

    def _handle_keydown_event(self, event: Event) -> None:
        key = event.key

        if key in keybind.ESCAPE and self._killable:
            self.kill()
            return
        elif key in keybind.SEND and self._editable:
            self._trigger.onSend(self, self._text)
        elif (direction := keybind.key_to_direction(key)) is not None:
            self._text_sprite.scroll(direction)
        elif self._editable:
            self._handle_edit_keydown_event(event)

    def _handle_edit_keydown_event(self, event: Event) -> None:
        assert self._editable

        if event.key == keybind.BACKSPACE:
            self.set_text(self._text[:-1])
        elif (unicode := event.unicode) == "":
            return
        else:
            self.set_text(self._text + unicode)


class TextSprite(WidgetSprite):

    def __init__(self,
                 background_image: Surface,
                 text: str = "",
                 font: Font | None = None,
                 ) -> None:

        super().__init__(background_image)
        self._text = text

        self._font = font if font is not None else SysFont(None, size=14)
        self._font.origin = True
        self._font_size_base: float = self._font.size

        self._render_data: list[_WordRenderData] = []
        cell_size = self._calculate_cell_size()
        self._scroller: Scroller[_WordRenderData] = Scroller(self._render_data,
                                                             self.rect.size,
                                                             cell_size)
        
        self._is_dirty = True if text != "" else False

        

    @override
    def scale(self, factor: pair) -> None:
        if factor == self._scale_factor:
            return

        super().scale(factor)
        self._font.size = self._font_size_base * factor[1]

    def set_text(self, new_text: str) -> None:
        if self._text == new_text:
            return

        self._text = new_text
        self._is_dirty = True

    def can_scroll(self, direction: Direction) -> bool:
        return self._scroller.can_scroll(direction)

    def scroll(self, direction: Direction, count: int = 1) -> None:
        if not self._scroller.can_scroll(direction):
            return

        self._scroller.scroll(direction)
        self._is_dirty = True

    def update(self, dt: float) -> None:
        if not self._is_dirty:
            return
        
        super().update(dt)
        self._render_data = self._wrap_text(self._text)
        self._scroller.set_area_size(self.rect.size)
        self._scroller.set_cell_size(self._calculate_cell_size())
        self._scroller.set_data(self._render_data)
        self._scroller.fit_unused_space()
        self._render()

        self._is_dirty = False

    def _calculate_cell_size(self) -> pair:
        width = self.rect.width
        try:
            height = self._render_data[0].size[1]
        except IndexError:
            height = self._font.get_sized_height() + 2
        return (width, height)

    def _wrap_text(self, text: str) -> list[_WordRenderData]:
        with WordWrapper(self._font, self.rect) as wrapper, WordStylist() as stylist:
            def assign_data(word_as_str: str) -> _WordRenderData:
                word = _WordRenderData(word_as_str)
                word = stylist.stylize(word)
                word = wrapper.wrap(word)
                return word

            words = [assign_data(word) for word in text.split(" ")]
        return words

    def _render(self) -> None:
        for word in self._scroller.get_visible():
            self._font.render_to(surf=self.image,
                                 dest=word.offset,
                                 text=word.text,
                                 style=word.style,
                                 fgcolor=word.fgcolor)


class ScrollData(Protocol):

    offset: pair
    size: pair


ScrollType = TypeVar("ScrollType", bound=ScrollData)


class Scroller(Generic[ScrollType]):

    def __init__(self,
                 data: list[ScrollType],
                 area_size: pair,
                 cell_size: pair,
                 ) -> None:

        self._data = data
        self._area = Rect(0, 0, *area_size)
        self._cell_size = cell_size
        self._position = (0, 0)


    def set_data(self, new_data: list[ScrollType]) -> None:
        self._data = new_data
        for item in self._data:
            item.offset = self._calculate_adjusted_offset(item)

    def set_area_size(self, new_size: pair) -> None:
        self._area = Rect(0, 0, *new_size)

    def set_cell_size(self, new_size: pair) -> None:
        shift = tuple_math.sub(self._cell_size, new_size)
        for item in self._data:
            item.offset = tuple_math.add(item.offset, shift)
        self._cell_size = new_size

    def can_scroll(self, direction: Direction) -> bool:
        if direction is Direction.UP:
            return self._position[1] > 0

        if direction is Direction.LEFT:
            return self._position[0] > 0

        try:
            last_item = self._data[-1]
        except IndexError:
            return False

        offset = self._calculate_adjusted_offset(last_item)

        if direction is Direction.DOWN:
            bottom = offset[1] + last_item.size[1]
            return bottom > self._area.height

        if direction is Direction.RIGHT:
            right = offset[0] + last_item.size[0]
            return right > self._area.width

        # Cannot scroll diagonally.
        return False

    def scroll(self, direction: Direction) -> None:
        if direction is Direction.DOWN:
            scroll = (0, 1)
        elif direction is Direction.UP:
            scroll = (0, -1)
        elif direction is Direction.RIGHT:
            scroll = (1, 0)
        elif direction is Direction.LEFT:
            scroll = (-1, 0)
        else:
            return
        
        shift = tuple_math.mult(self._cell_size, scroll)
        for item in self._data:
            item.offset = tuple_math.add(item.offset, shift)
        
        self._position = tuple_math.add(self._position, scroll)

    def fit_unused_space(self) -> None:
        try:
            last_item = self._data[-1]
        except IndexError:
            self._position = (0, 0)
            return
        
        end = tuple_math.add(last_item.size,
            self._calculate_adjusted_offset(last_item))
        unused_area = tuple_math.sub(self._area.size, end)
        unused_area = tuple(x if x >= 0 else 0 for x in unused_area)

        def round_negative(value: int) -> int:
            return value if value >= 0 else 0
        
        self._position = tuple(round_negative(pos - int(unused // cell)) for (pos, unused, cell) in zip(self._position,
                                                                                                                   unused_area,
                                                                                                                   self._area.size))

    def get_visible(self) -> list[ScrollType]:
        return [item for item in self._data if self.is_visible(item)]

    def is_visible(self, item: ScrollType) -> bool:
        offset = tuple_math.sub(item.offset,
                                (0, self._cell_size[1]))
        item_rect = Rect(*offset, *item.size)
        return self._area.colliderect(item_rect)
        

    @property
    def _scroll_offset(self) -> pair:
        return tuple_math.mult(self._cell_size, self._position)

    def _calculate_adjusted_offset(self, item: ScrollType) -> pair:
        return tuple_math.sub(item.offset, self._scroll_offset)


@dataclass
class _WordRenderData(ScrollData):

    text: str = ""
    offset: pair = (0, 0)
    fgcolor: str | None = None
    style: int = 0
    size: pair = (0, 0)


class WordWrapper:
    """
    WordWrapper ensures the actual wrapper (implemented as an inner class _Wrapper) is only called via context management.
    The actual wrapper relies on temporary variables which update after each `wrap()` call and should be reset when the entire text is wrapped.
    """

    def __init__(self, font: Font, area: Rect) -> None:
        area_width = area.width
        spacing = (font.get_rect(" ").width, 2)
        self._wrapper = self._Wrapper(font, area_width, spacing)

    def __enter__(self) -> WordWrapper._Wrapper:
        self._wrapper.start()
        return self._wrapper

    def __exit__(self, *args: object, **kwargs: object) -> None:
        self._wrapper.stop()
        del self._wrapper

    class _Wrapper:

        def __init__(self, font: Font, area_width: float, spacing: pair) -> None:
            assert font.origin
            self.font = font
            self.area_width = area_width
            self.spacing = spacing

        def start(self) -> None:
            self.x = 0
            self.y = 0
            self.linebreak_found = False

        def stop(self) -> None:
            del self.x, self.y, self.linebreak_found

        def wrap(self, word_data: _WordRenderData) -> _WordRenderData:
            clean_text = word_data.text.rstrip("\n")
            width = self.font.get_rect(clean_text).width
            height = self.font.get_sized_height() + self.spacing[1]

            # Break the line if the word does not fit the area width
            # or if the linebreak character has been found on the previous wrap call.
            if (self.x + width > self.area_width
                    or self.linebreak_found):
                self.linebreak_found = False
                self.x = 0
                self.y += height

            if word_data.text != "":
                width += self.spacing[0]

            if word_data.text.endswith("\n"):
                self.linebreak_found = True

            word_data.offset = (self.x, self.y)
            word_data.text = clean_text
            word_data.size = (width, height)

            self.x += width
            return word_data


class WordStylist:

    def __init__(self) -> None:
        self._stylist = self._Stylist()

    def __enter__(self) -> WordStylist._Stylist:
        self._stylist.start()
        return self._stylist

    def __exit__(self, *args: object, **kwargs: object) -> None:
        self._stylist.stop()
        del self._stylist

    class _Stylist(HTMLParser):

        def start(self) -> None:
            self.tags = {"i": False,
                         "b": False,
                         "u": False}
            self.color: str | None = None

            self.found_end_tags: list[str] = []
            self.markdown_incomplete = False

        def stop(self) -> None:
            del self.tags, self.found_end_tags, self.color, self.markdown_incomplete

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag == "font":
                self.color = next(
                    value for key, value in attrs if key == "color")
            else:
                self.tags[tag] = True

        def handle_endtag(self, tag: str) -> None:
            self.found_end_tags.append(tag)

        def stylize(self, word: _WordRenderData) -> _WordRenderData:
            text = word.text
            self.found_end_tags = []

            # Feed a space in case the markdown is incomplete and should not be merged with the following words.
            self.feed(text + " ")

            word.style = (pygame.freetype.STYLE_OBLIQUE * int(self.tags["i"])
                          | pygame.freetype.STYLE_STRONG * int(self.tags["b"])
                          | pygame.freetype.STYLE_UNDERLINE * int(self.tags["u"]))
            word.text = self._remove_tags(text)
            word.fgcolor = self.color

            for tag in self.found_end_tags:
                if tag == "font":
                    self.color = None
                else:
                    self.tags[tag] = False

            return word

        def _remove_tags(self, word: str) -> str:
            if self.markdown_incomplete:
                if ">" in word:
                    self.markdown_incomplete = False
                return word.partition(">")[2]

            regex = "<.*?>"
            word = re.sub(regex, "", word)

            if "<" in word:
                self.markdown_incomplete = True
                return word.partition("<")[0]

            return word
