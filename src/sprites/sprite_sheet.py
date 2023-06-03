from os import PathLike
from typing import Any

import pygame as pg
from pygame import Surface


class SpriteSheet:

    def __init__(self, image_path: PathLike[Any] | str, alpha: bool = False) -> None:
        if alpha:
            self._sheet = pg.image.load(
                image_path).convert_alpha()
        else:
            self._sheet = pg.image.load(image_path).convert()

        self.alpha = alpha

    @property
    def size(self) -> tuple[int, int]:
        return self._sheet.get_size()

    def extract_whole(self, alpha: bool | None = None, colorkey: Any | None = None) -> Surface:
        rect = self._sheet.get_rect()
        return self.extract_image(rect=rect, alpha=alpha, colorkey=colorkey)

    def extract_image(self,
                      rect: Any,
                      alpha: bool | None = None,
                      colorkey: Any | None = None,
                      ) -> Surface:

        if alpha is None:
            alpha = self.alpha

        if alpha and colorkey:
            raise ValueError("Cannot accept both alpha and colorkey.")

        width, height = rect[2:4]

        if alpha:
            image = Surface((width, height), pg.SRCALPHA).convert_alpha()
            image.fill((0, 0, 0, 0))
        else:
            image = Surface((width, height)).convert()

        if colorkey:
            image.set_colorkey(colorkey, pg.RLEACCEL)

        image.blit(self._sheet, (0, 0), rect)

        return image

    def split(self,
              size: tuple[int, int],
              alpha: bool | None = None,
              colorkey: Any | None = None,
              ) -> list[Surface]:

        width, height = size[0], size[1]

        rects = [(x, y, width, height)
                 for y in range(0, self._sheet.get_height(), height)
                 for x in range(0, self._sheet.get_width(), width)]

        return [self.extract_image(r, alpha, colorkey) for r in rects]
