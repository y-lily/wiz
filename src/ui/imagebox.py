import pygame as pg
from pygame.surface import Surface

from . import keybind
from .blueprint import WidgetTrigger
from .widget import Widget, WidgetSprite


class Imagebox(Widget):

    def __init__(self,
                 bg_texture: Surface,
                 image: Surface,
                 trigger: WidgetTrigger,
                 killable: bool = True,
                 ) -> None:

        super().__init__(bg_texture, trigger)

        self._image_sprite = WidgetSprite(image)
        self._image_sprite.centered = True
        self._spritegroup.add(self._image_sprite)

        self._killable = killable

    def set_image(self, new_image: Surface) -> None:
        self._image_sprite.image = new_image

    def handle_inputs(self) -> None:
        # Delegate input handling to the top child if it is present and wants input.
        super().handle_inputs()

        # If the event queue is not empty after the delegation attempt, the widget
        # is free to handle inputs on its own.
        for event in pg.event.get(eventtype=(pg.KEYDOWN)):
            if event.key in keybind.ESCAPE and self._killable:
                self.kill()
