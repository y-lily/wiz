from __future__ import annotations

from abc import ABC, abstractmethod

import pygame as pg
from pygame.rect import Rect
from pygame.sprite import OrderedUpdates, Sprite
from pygame.surface import Surface
from typing_extensions import override

from . import tuple_math
from .blueprint import WidgetTrigger
from .shared import pair


class WidgetStack(ABC):

    def __init__(self) -> None:
        self._widgets: list[Widget] = []
        self._scale_factor = (1.0, 1.0)
        self._needs_reposition = False

    def add(self,
            widget: Widget,
            centered: bool = False,
            offset: pair = (0.0, 0.0),
            ) -> None:

        self._widgets.append(widget)
        widget.add_internal(self)

        widget.centered = centered
        widget.set_offset_base(offset)
        widget.scale(self._scale_factor)

        self._needs_reposition = True

    def remove(self, widget: Widget) -> None:
        self._widgets.remove(widget)
        widget.remove_internal(self)

    def scale(self, factor: pair) -> None:
        self._scale_factor = factor

        for widget in self._widgets:
            widget.scale(factor)

        self._needs_reposition = True

    def handle_inputs(self) -> None:
        try:
            top = self._widgets[-1]
        except IndexError:
            return

        top.handle_inputs()

    @abstractmethod
    def update(self, dt: float) -> None:
        for widget in self._widgets:
            widget.update(dt)


class Widget(WidgetStack):

    centered: bool = False
    _parent: WidgetStack

    def __init__(self,
                 bg_texture: Surface,
                 trigger: WidgetTrigger,
                 ) -> None:

        super().__init__()
        self._spritegroup = OrderedUpdates()
        self._background = WidgetSprite(bg_texture)
        self._spritegroup.add(self._background)

        self._trigger = trigger
        self._offset_base = (0.0, 0.0)

    @override
    def scale(self, factor: pair) -> None:
        super().scale(factor)

        for sprite in self._spritegroup:
            sprite.scale(factor)

    @override
    def update(self, dt: float) -> None:
        super().update(dt)

        self._spritegroup.update(dt)

        if self._needs_reposition:
            self._reposition()

        self._needs_reposition = False

    def draw(self, surface: Surface) -> None:
        self._spritegroup.draw(surface)

        for widget in self._widgets:
            widget.draw(surface)

    def calculate_offset(self) -> pair:
        return tuple_math.mult(self._offset_base,
                                   self._scale_factor)

    def set_offset_base(self, new_base: pair) -> None:
        self._offset_base = new_base

    def center_at(self, position: pair) -> None:
        self._background.center_at(position)
        self._needs_reposition = True

    def position_at(self, position: pair) -> None:
        self._background.position_at(position)
        self._needs_reposition = True

    def get_size(self) -> pair:
        return self._background.rect.size

    def add_internal(self, parent: WidgetStack) -> None:
        self._parent = parent

    def remove_internal(self, parent: WidgetStack) -> None:
        assert parent == self._parent
        del self._parent

    def kill(self) -> None:
        self._trigger.onKill(self)

        for widget in self._widgets:
            widget.kill()
        for sprite in self._spritegroup:
            sprite.kill()

        try:
            parent = self._parent
        except AttributeError:
            return

        parent.remove(self)

    def _reposition(self) -> None:
        rect = self._background.rect
        center = rect.center
        topleft = rect.topleft

        def update_position(child: Widget | WidgetSprite) -> None:
            if child.centered:
                child.center_at(center)
            else:
                position = tuple_math.add(topleft,
                                          child.calculate_offset())
                child.position_at(position)

        for widget in self._widgets:
            update_position(widget)
        for sprite in self._spritegroup:
            update_position(sprite)


class UI(WidgetStack):

    def __init__(self, screen: Surface) -> None:
        super().__init__()
        self._screen = screen

    @override
    def update(self, dt: float) -> None:
        super().update(dt)

        if self._needs_reposition:
            self._reposition()

        self._needs_reposition = False

    def draw(self) -> None:
        for widget in self._widgets:
            widget.draw(self._screen)

    def set_screen(self, new_screen: Surface) -> None:
        self._screen = new_screen

    def _reposition(self) -> None:
        rect = self._screen.get_rect()
        center = rect.center
        topleft = rect.topleft

        def update_position(child: Widget | WidgetSprite) -> None:
            if child.centered:
                child.center_at(center)
            else:
                position = tuple_math.add(topleft,
                                          child.calculate_offset())
                child.position_at(position)

        for widget in self._widgets:
            update_position(widget)


class WidgetSprite(Sprite):

    centered: bool = False
    rect: Rect

    def __init__(self, image: Surface) -> None:
        super().__init__()

        self._image = image
        self._refresher = image.copy()
        self.rect = image.get_rect()

        self._scale_factor = (1.0, 1.0)
        self._offset_base = (0.0, 0.0)
        self._is_dirty = True

    @property
    def image(self) -> Surface:
        return self._image

    @image.setter
    def image(self, new_image: Surface) -> None:
        self._refresher = new_image.copy()
        self._is_dirty = True

    def calculate_offset(self) -> pair:
        return tuple_math.mult(self._offset_base,
                                   self._scale_factor)

    def set_offset_base(self, new_base: pair) -> None:
        self._offset_base = new_base

    def center_at(self, position: pair) -> None:
        self.rect.center = position

    def position_at(self, position: pair) -> None:
        self.rect.topleft = position

    def scale(self, factor: pair) -> None:
        if factor == self._scale_factor:
            return

        self._scale_factor = factor
        self._is_dirty = True

    def update(self, dt: float) -> None:
        if not self._is_dirty:
            return

        image_size = tuple_math.mult(self._refresher.get_size(),
                                         self._scale_factor)
        self._image = pg.transform.smoothscale(self._refresher,
                                               image_size)
        self.rect = Rect(*self.rect.topleft, *self._image.get_size())

        self._is_dirty = False
