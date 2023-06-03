import pygame as pg
from pygame import Surface
from pygame.event import Event
from pygame.freetype import Font, SysFont
from typing_extensions import override

from . import keybind, shared
from .shared import Direction, pair
from .textbox import TextSprite, create_default_font
from .widget import Widget, WidgetSprite, WidgetTrigger


class Dialogue(Widget):

    def __init__(self,
                 text: str,
                 portrait: Surface,
                 header: str,
                 bg: Surface,
                 trigger: WidgetTrigger,
                 padding: tuple[int, int, int, int],
                 spacing: pair[int] = (8, 20),
                 font: Font | None = None,
                 editable: bool = False,
                 closeable: bool = True,
                 ) -> None:

        super().__init__(bg, trigger)

        self._text = text
        self._editable = editable
        self._closeable = closeable

        surf_size = shared.calculate_subsurface_size(bg, padding)
        self._dialogue_sprite = DialogueSprite(
            surf_size, portrait, text, header, spacing, font)
        self._dialogue_sprite.set_offset_base(padding[:2])
        self._sprites.add(self._dialogue_sprite)

    @override
    def handle_inputs(self) -> None:
        super().handle_inputs()

        for event in pg.event.get(eventtype=pg.KEYDOWN):
            self._handle_keydown_event(event)

    @property
    def typing_mode(self) -> bool:
        return self._editable

    @typing_mode.setter
    def typing_mode(self, new_value: bool) -> None:
        self._editable = new_value

    def set_params(self,
                   new_text: str | None = None,
                   new_header: str | None = None,
                   new_portrait: Surface | None = None,
                   ) -> None:

        # Setters are combined because it is often required to switch
        # multiple parameters at once.

        if new_text is not None:
            self._text = new_text
            self._dialogue_sprite.set_text(new_text)
        if new_header is not None:
            self._dialogue_sprite.set_header(new_header)
        if new_portrait is not None:
            self._dialogue_sprite.set_portrait(new_portrait)

    def _handle_keydown_event(self, event: Event) -> None:
        if (key := event.key) in keybind.ESCAPE and self._closeable:
            self.kill()
            return
        elif key in keybind.SEND and self._editable:
            self._trigger.onSend(self, self._text)
        elif key in keybind.USE and not self._editable:
            self._trigger.onUse(self)
        elif (direction := keybind.key_to_direction(key)) is not None:
            self._dialogue_sprite.scroll(direction)
        elif self._editable:
            self._handle_edit_event(event)

    def _handle_edit_event(self, event: Event) -> None:
        assert self._editable

        if event.key in keybind.BACKSPACE:
            self.set_params(new_text=self._text[:-1])
        elif (unicode := event.unicode) == "":
            return
        else:
            self.set_params(new_text=self._text + unicode)


class DialogueSprite(WidgetSprite):

    def __init__(self,
                 size: pair[int],
                 portrait: Surface,
                 text: str,
                 header: str,
                 spacing: pair[int],
                 font: Font | None = None,
                 ) -> None:

        image = shared.build_transparent_surface(size)
        super().__init__(image)

        self._portrait = WidgetSprite(portrait)
        self._sprites.add(self._portrait)

        self._font = font if font is not None else create_default_font()
        self._font.origin = True
        assert isinstance(self._font.size, float)
        self._font_size_base = self._font.size

        self._header_font_size_base = self._font_size_base + 2
        self._header_font = SysFont(
            self._font.name, self._header_font_size_base, bold=True)

        header_offset_x = portrait.get_width() + spacing[0]
        header_size = (image.get_width() - header_offset_x,
                       self._header_font.get_sized_height() + 4)
        self._header = TextSprite(header_size, header, self._header_font)
        self._header.set_offset_base((header_offset_x, 0))
        self._sprites.add(self._header)

        body_offset_x = header_offset_x
        body_offset_y = header_size[1] + spacing[1]
        body_size = (header_size[0],
                     image.get_height() - body_offset_y)
        self._body = TextSprite(body_size, text)
        self._body.set_offset_base((body_offset_x, body_offset_y))
        self._sprites.add(self._body)

    def can_scroll(self, direction: Direction) -> bool:
        return self._body.can_scroll(direction)

    def scroll(self, direction: Direction) -> None:
        self._body.scroll(direction)

    def set_header(self, new_header: str) -> None:
        self._header.set_text(new_header)

    def set_portrait(self, new_portrait: Surface) -> None:
        # TODO: Deal with the potential size mismatch.
        self._portrait.image = new_portrait

    def set_text(self, new_text: str) -> None:
        self._body.set_text(new_text)
