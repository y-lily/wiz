from __future__ import annotations

import pygame as pg
from pygame import Rect, Surface
from pygame.event import Event
from pygame.freetype import Font, SysFont
from typing_extensions import override

# TODO:
# import keybind, shared
# from shared import Direction, pair
from src import keybind, shared
from src.shared import Direction, pair

from .widget import Widget, WidgetSprite, WidgetTrigger


class Textbox(Widget):

    def __init__(self,
                 text: str,
                 bg: Surface,
                 trigger: WidgetTrigger,
                 padding: tuple[int, int, int, int],
                 font: Font | None = None,
                 editable: bool = False,
                 closeable: bool = True,
                 ) -> None:

        super().__init__(bg, trigger)

        self._text = text
        self._editable = editable
        self._closeable = closeable

        surf_size = shared.calculate_subsurface_size(bg, padding)
        self._text_sprite = TextSprite(surf_size, text, font)
        self._text_sprite.set_offset_base(padding[:2])
        self._sprites.add(self._text_sprite)

    @override
    def handle_inputs(self) -> None:
        super().handle_inputs()

        for event in pg.event.get(eventtype=(pg.KEYDOWN)):
            self._handle_keydown_event(event)

    def set_text(self, new_text: str) -> None:
        self._text = new_text
        self._text_sprite.set_text(new_text)

    def _handle_keydown_event(self, event: Event) -> None:
        if (key := event.key) in keybind.ESCAPE and self._closeable:
            self.kill()
            return
        elif key in keybind.SEND and self._editable:
            self._trigger.onSend(self, self._text)
        elif key in keybind.USE and not self._editable:
            self._trigger.onUse(self)
        elif (direction := keybind.key_to_direction(key)) is not None:
            self._text_sprite.scroll(direction)
        elif self._editable:
            self._handle_edit_event(event)

    def _handle_edit_event(self, event: Event) -> None:
        assert self._editable

        if event.key in keybind.BACKSPACE:
            self.set_text(self._text[:-1])
        elif (unicode := event.unicode) == "":
            return
        else:
            self.set_text(self._text + unicode)


class TextSprite(WidgetSprite):

    _scroll_step: pair[int]
    _text_surface: Surface

    def __init__(self,
                 size: pair[int],
                 text: str = "",
                 font: Font | None = None,
                 ) -> None:

        image = shared.build_transparent_surface(size)
        super().__init__(image)
        self._text = text
        self._font = font if font is not None else create_default_font()
        self._font.origin = True

        assert isinstance(self._font.size, float)
        self._font_size_base = self._font.size
        self._display_position = (0, 0)
        self._wrapper = TextWrapper(self._text, self._font)

        self._update_scroll_step()
        self._update_text_surface()

    @override
    def scale(self, factor: pair[float]) -> None:
        super().scale(factor)
        self._font.size = self._font_size_base * factor[1]
        self._update_scroll_step()
        self._update_text_surface()

    @override
    def update(self, dt: float) -> None:
        super().update(dt)

        self._adjust_position()
        area = Rect(*self._display_position,
                    *self.rect.size)
        self._image.blit(self._text_surface,
                         (0, 0),
                         area)

    def can_scroll(self, direction: Direction) -> bool:
        x, y = self._display_position

        if direction is Direction.UP:
            return y > 0
        elif direction is Direction.LEFT:
            return x > 0
        elif direction is Direction.DOWN:
            return y + self.rect.height < self._text_surface.get_height()
        elif direction is Direction.RIGHT:
            return x + self.rect.width < self._text_surface.get_width()

        return False

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

    def set_text(self, new_text: str) -> None:
        if self._text == new_text:
            return

        self._text = new_text
        self._wrapper.set_text(new_text)
        self._update_text_surface()

    def _adjust_position(self) -> None:
        max_x = self._text_surface.get_width() - self.rect.width
        max_y = self._text_surface.get_height() - self.rect.height
        x, y = self._display_position

        x = max(0, min(x, max_x))
        y = max(0, min(y, max_y))

        self._display_position = (x, y)

    def _update_scroll_step(self) -> None:
        self._scroll_step = self._font.get_rect("12").size

    def _update_text_surface(self) -> None:
        # Do not use the current rect.width as it may change after update.
        width = self._refresher.get_width() * self._scale_factor[0]
        self._text_surface = self._wrapper.make_surface(int(width))


# class DialogueSprite(WidgetSprite):

#     def __init__(self,
#                  image: Surface,
#                  portrait: Surface,
#                  text: str,
#                  width_spacing: int,
#                  font: Font | None = None,
#                  ) -> None:

#         super().__init__(image)

#         self._portrait_child = WidgetSprite(portrait)
#         # self._children.append(self._portrait_child)
#         self._children.add(self._portrait_child)

#         text_start = portrait.get_width() + width_spacing

#         text_surface = shared.build_transparent_surface(
#             tuple_math.sub(image.get_size(), (text_start, 0))
#         )

#         self._text_child = TextSprite(text_surface, text, font)
#         self._text_child.set_offset_base((text_start, 0))
#         # self._children.append(self._text_child)
#         self._children.add(self._text_child)

#     def can_scroll(self, direction: Direction) -> bool:
#         return self._text_child.can_scroll(direction)

#     def scroll(self, direction: Direction) -> None:
#         self._text_child.scroll(direction)
#         self._dirty = True

#     def set_portrait(self, new_portrait: Surface) -> None:
#         self._portrait_child.image = new_portrait
#         self._dirty = True

#     def set_text(self, new_text: str) -> None:
#         self._text_child.set_text(new_text)
#         self._dirty = True


class TextWrapper:

    def __init__(self,
                 text: str,
                 font: Font,
                 ) -> None:

        self._text = text
        self._font = font

    def make_surface(self,
                     base_width: int = 0,
                     height_spacing: int = 2,
                     ) -> Surface:

        def clean(word: str) -> str:
            return word.rstrip("\n")

        def make_rect(word: str) -> Rect:
            return self._font.get_rect(word)

        words = [(word, make_rect(clean(word)))
                 for word in self._text.split(" ")]
        surface_width = max(base_width,
                            max(rect.width for _, rect in words))
        space_width = self._font.get_rect(" ").width
        row_height = self._font.get_sized_height()

        x = 0
        y = row_height

        def next_row() -> None:
            nonlocal x, y
            x = 0
            y += row_height + height_spacing

        for word, rect in words:
            width = rect.width

            if x + width > surface_width:
                next_row()

            rect.topleft = (x, y)
            x += width + space_width

            if word.endswith("\n"):
                next_row()

        surface_height = y + row_height
        surface = shared.build_transparent_surface(
            (surface_width, surface_height))

        for word, rect in words:
            self._font.render_to(surface, rect.topleft, clean(word))

        return surface

    def set_text(self, new_text: str) -> None:
        self._text = new_text


# class WordStylist:

#     def __init__(self) -> None:
#         self._stylist = self._Stylist()

#     def __enter__(self) -> WordStylist._Stylist:
#         self._stylist.start()
#         return self._stylist

#     def __exit__(self, *args: object, **kwargs: object) -> None:
#         self._stylist.stop()
#         del self._stylist

#     class _Stylist(HTMLParser):

#         def start(self) -> None:
#             self.tags = {"i": False,
#                          "b": False,
#                          "u": False}
#             self.color: str | None = None

#             self.found_end_tags: list[str] = []
#             self.markdown_incomplete = False

#         def stop(self) -> None:
#             del self.tags, self.found_end_tags, self.color, self.markdown_incomplete

#         def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
#             if tag == "font":
#                 self.color = next(
#                     value for key, value in attrs if key == "color")
#             else:
#                 self.tags[tag] = True

#         def handle_endtag(self, tag: str) -> None:
#             self.found_end_tags.append(tag)

#         def stylize(self, word: _WordRenderData) -> _WordRenderData:
#             text = word.text
#             self.found_end_tags = []

#             # Feed a space in case the markdown is incomplete and should not be merged with the following words.
#             self.feed(text + " ")

#             word.style = (pygame.freetype.STYLE_OBLIQUE * int(self.tags["i"])
#                           | pygame.freetype.STYLE_STRONG * int(self.tags["b"])
#                           | pygame.freetype.STYLE_UNDERLINE * int(self.tags["u"]))
#             word.text = self._remove_tags(text)
#             word.fgcolor = self.color

#             for tag in self.found_end_tags:
#                 if tag == "font":
#                     self.color = None
#                 else:
#                     self.tags[tag] = False

#             return word

#         def _remove_tags(self, word: str) -> str:
#             if self.markdown_incomplete:
#                 if ">" in word:
#                     self.markdown_incomplete = False
#                 return word.partition(">")[2]

#             regex = "<.*?>"
#             word = re.sub(regex, "", word)

#             if "<" in word:
#                 self.markdown_incomplete = True
#                 return word.partition("<")[0]

#             return word

def create_default_font() -> Font:
    return SysFont("Arial", 14)
