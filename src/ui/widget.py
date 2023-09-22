from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable, ClassVar

import pygame as pg
import tuple_math
from pygame import Rect, Surface
from pygame.sprite import OrderedUpdates, Sprite
from transitions import core
from tuple_math import pair
from typing_extensions import override

from src import shared
from src.shared import no_op


class WidgetStack(ABC):

    def __init__(self) -> None:
        self._widgets: list[Widget] = []
        self._scale_factor = (1.0, 1.0)
        self._needs_reposition = False

    def add(self,
            widget: Widget,
            centered: bool | None = None,
            offset: pair[float] | None = None,
            ) -> None:

        self._widgets.append(widget)
        widget.add_internal(self)

        if centered is not None:
            widget.centered = centered
        if offset is not None:
            widget.set_offset_base(offset)
        widget.scale(self._scale_factor)

        self.request_reposition()

    def handle_inputs(self) -> None:
        try:
            top = self._widgets[-1]
        except IndexError:
            return

        top.handle_inputs()

    def remove(self, widget: Widget) -> None:
        self._widgets.remove(widget)
        widget.remove_internal(self)

    def request_reposition(self) -> None:
        self._needs_reposition = True

    def scale(self, factor: pair[float]) -> None:
        self._scale_factor = factor

        for widget in self._widgets:
            widget.scale(factor)

        self.request_reposition()

    @abstractmethod
    def update(self, dt: float) -> None:
        if self._needs_reposition:
            self._reposition()

        self._needs_reposition = False

        # Use a copy of the list since the widgets may be removed
        # from the original list during the iteration.
        for widget in list(self._widgets):
            widget.update(dt)

    @abstractmethod
    def _reposition(self) -> None:
        raise NotImplementedError


class Widget(WidgetStack):

    _parent: WidgetStack

    def __init__(self,
                 bg: Surface,
                 trigger: WidgetTrigger,
                 ) -> None:

        super().__init__()

        self._sprites: OrderedUpdates[WidgetSprite] = OrderedUpdates()
        self._bg = WidgetSprite(bg)
        self._sprites.add(self._bg)

        self._trigger = trigger
        self._offset_base = (0.0, 0.0)
        self._centered = False

    @property
    def centered(self) -> bool:
        return self._centered

    @centered.setter
    def centered(self, new_value: bool) -> None:
        self._centered = new_value
        self.request_reposition()

    @override
    def request_reposition(self) -> None:
        super().request_reposition()

        try:
            parent = self._parent
        except AttributeError:
            return

        parent.request_reposition()

    @override
    def scale(self, factor: pair[float]) -> None:
        super().scale(factor)

        for sprite in self._sprites:
            sprite.scale(factor)

    @override
    def update(self, dt: float) -> None:
        super().update(dt)

        self._sprites.update(dt)

    @override
    def _reposition(self) -> None:
        rect = self._bg.rect
        center = rect.center
        topleft = rect.topleft

        def reposition(child: Widget | WidgetSprite) -> None:
            if child.centered:
                child.center_at(center)
            else:
                position = tuple_math.add(topleft,
                                          child.calculate_offset())
                child.position_at(tuple_math.intify(position))

        for widget in self._widgets:
            reposition(widget)
        for sprite in self._sprites:
            reposition(sprite)

    def add_internal(self, parent: WidgetStack) -> None:
        assert not hasattr(self, "_parent")
        self._parent = parent

    def calculate_offset(self) -> pair[float]:
        return tuple_math.mult(self._offset_base,
                               self._scale_factor)

    def center_at(self, pixel: pair[int]) -> None:
        self._bg.center_at(pixel)

        # This method moves the widget directly and is used by
        # its parent. Therefore, request_reposition() should not be
        # called here as it will cause recursion.
        self._reposition()

    def draw(self, surface: Surface) -> list[Rect]:
        rects = list(core.listify(self._sprites.draw(surface)))

        for widget in self._widgets:
            rects += core.listify(widget.draw(surface))

        return rects

    def get_size(self) -> pair[int]:
        return self._bg.rect.size

    def kill(self) -> None:
        self._trigger.onKill(self)

        for widget in list(self._widgets):
            widget.kill()

        self._widgets = []
        self._sprites.empty()

        try:
            parent = self._parent
        except AttributeError:
            return

        parent.remove(self)

    def move(self, step: pair[int]) -> None:
        position = tuple_math.add(self._bg.rect.topleft,
                                  step)
        self.position_at(position)

    def position_at(self, pixel: pair[int]) -> None:
        self._bg.position_at(pixel)

        # This method moves the widget directly and is used by
        # its parent. Therefore, request_reposition() should not be
        # called here as it will cause recursion.
        self._reposition()

    def remove_internal(self, parent: WidgetStack) -> None:
        assert parent is self._parent
        del self._parent

    def set_offset_base(self, new_base: pair[float]) -> None:
        self._offset_base = new_base
        self.request_reposition()

    def shift_offset_base(self, shift: pair[int]) -> None:
        self._offset_base = tuple_math.add(self._offset_base,
                                           shift)
        self.request_reposition()


class UI(WidgetStack):

    def __init__(self, screen: Surface) -> None:
        super().__init__()
        self._screen = screen

    @override
    def update(self, dt: float) -> None:
        super().update(dt)

    @override
    def _reposition(self) -> None:
        rect = self._screen.get_rect()
        center = rect.center
        topleft = rect.topleft

        def reposition(child: Widget | WidgetSprite) -> None:
            if child.centered:
                child.center_at(center)
            else:
                position = tuple_math.add(topleft,
                                          child.calculate_offset())
                child.position_at(tuple_math.intify(position))

        for widget in self._widgets:
            reposition(widget)

    def draw(self) -> list[Rect]:
        rects: list[Rect] = []

        for widget in self._widgets:
            rects += core.listify(widget.draw(self._screen))

        return rects

    def set_screen(self, new_screen: Surface) -> None:
        self._screen = new_screen
        self.request_reposition()


class WidgetSprite(Sprite):

    centered: bool = False
    rect: Rect
    _highlighter: Highlighter

    def __init__(self, image: Surface) -> None:
        super().__init__()

        self._image = image
        self._refresher = image.copy()
        self.rect = image.get_rect()

        self._offset_base = (0.0, 0.0)
        self._scale_factor = (1.0, 1.0)

        self._sprites: OrderedUpdates[WidgetSprite] = OrderedUpdates()

        if not isinstance(self, Highlighter):
            self._highlighter = Highlighter(self.rect.size)
            self._sprites.add(self._highlighter)

    @property
    def image(self) -> Surface:
        """NB: in-place changes on the image (e.g., `sprite.image.fill(...)`)
        will not have any effect. Use `sprite.image = new_image` instead."""
        return self._image

    @image.setter
    def image(self, new_image: Surface) -> None:
        self._refresher = new_image.copy()
        self._image = pg.transform.smoothscale(self._refresher,
                                               tuple_math.mult(self._refresher.get_size(),
                                                               self._scale_factor))

    def calculate_offset(self) -> pair[float]:
        return tuple_math.mult(self._offset_base,
                               self._scale_factor)

    def center_at(self, pixel: pair[int]) -> None:
        self.rect.center = pixel

    def highlight(self,
                  mode_on: bool = True,
                  *,
                  color: tuple[int, int, int, int] | None = None,
                  ) -> None:

        self._highlighter.set_mode(mode_on)
        if color is not None:
            self._highlighter.set_color(color)

    def position_at(self, pixel: pair[int]) -> None:
        self.rect.topleft = pixel

    def scale(self, factor: pair[float]) -> None:
        for sprite in self._sprites:
            sprite.scale(factor)
        self._scale_factor = factor

    def set_offset_base(self, new_base: pair[float]) -> None:
        self._offset_base = new_base

    def update(self, dt: float) -> None:
        self._sprites.update(dt)
        self._image = pg.transform.smoothscale(self._refresher,
                                               tuple_math.mult(self._refresher.get_size(),
                                                               self._scale_factor))
        self.rect.size = self._image.get_size()

        self._reposition_sprites()
        self._sprites.draw(self._image)

    def _reposition_sprites(self) -> None:
        center = self.rect.center

        for sprite in self._sprites:
            if sprite.centered:
                sprite.center_at(center)
            else:
                sprite.position_at(tuple_math.intify(
                    sprite.calculate_offset()))


class Highlighter(WidgetSprite):

    DEFAULT_COLOR: ClassVar = (255, 213, 51, 90)

    def __init__(self,
                 size: pair[int],
                 color: tuple[int, int, int, int] | None = None,
                 ) -> None:

        image = shared.build_transparent_surface(size)
        super().__init__(image)
        self._color = color if color is not None else self.DEFAULT_COLOR
        self._mode_on = False

    @override
    def highlight(self,
                  mode_on: bool = True,
                  *,
                  color: tuple[int, int, int, int] | None = None,
                  ) -> None:

        raise AttributeError(
            f"A highlighter object {self} cannot be highlighted.")

    @override
    def update(self, dt: float) -> None:
        self._image = pg.transform.smoothscale(self._refresher,
                                               tuple_math.mult(self._refresher.get_size(),
                                                               self._scale_factor))
        if self._mode_on:
            self._image.fill(self._color)

        self.rect.size = self._image.get_size()

    def set_color(self, color: tuple[int, int, int, int]) -> None:
        self._color = color

    def set_mode(self, mode_on: bool) -> None:
        self._mode_on = mode_on


class WidgetTrigger:

    def __init__(self,
                 on_kill: Callable[[WidgetTrigger, Widget], None]
                 | None = None,
                 on_send: Callable[[WidgetTrigger, Widget, Any], None]
                 | None = None,
                 on_use: Callable[[WidgetTrigger, Widget], None]
                 | None = None,
                 ) -> None:

        self._on_kill: Callable[[WidgetTrigger, Widget],
                                None] = on_kill if on_kill is not None else no_op
        self._on_send: Callable[[WidgetTrigger, Widget, Any],
                                None] = on_send if on_send is not None else no_op
        self._on_use: Callable[[WidgetTrigger, Widget],
                               None] = on_use if on_use is not None else no_op

    def onKill(self, widget: Widget) -> None:
        return self._on_kill(self, widget)

    def onSend(self, widget: Widget, data: Any) -> None:
        return self._on_send(self, widget, data)

    def onUse(self, widget: Widget) -> None:
        return self._on_use(self, widget)
