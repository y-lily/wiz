import pathlib
from typing import Optional, Sequence

import pygame
from pygame.surface import Surface

from .shared import RESOURCE_DIR, Path


class SpriteSheet:

    def __init__(self, image_path: Path, alpha: bool = False) -> None:
        if alpha:
            self._sheet = pygame.image.load(image_path).convert_alpha()
        else:
            self._sheet = pygame.image.load(image_path).convert()

    def image_at(self,
                 rect: tuple[int, ...],
                 alpha: bool = False,
                 colorkey: Optional[tuple[int, ...]] = None,
                 ) -> Surface:

        if alpha and colorkey:
            raise ValueError("Cannot accept both alpha and colorkey.")

        width, height = rect[2:4]

        if alpha:
            image = Surface((width, height), pygame.SRCALPHA)
        else:
            image = Surface((width, height)).convert()

        if colorkey:
            image.set_colorkey(colorkey, pygame.RLEACCEL)

        image.blit(self._sheet, (0, 0), rect)

        return image

    def images_at(self,
                  rects: Sequence[tuple[int, ...]],
                  alpha: bool = False,
                  colorkey: Optional[tuple[int, ...]] = None,
                  ) -> list[Surface]:

        return [self.image_at(rect, alpha, colorkey) for rect in rects]

    def split(self,
              rect: tuple[int, ...],
              alpha: bool = False,
              colorkey: Optional[tuple[int, ...]] = None,
              ) -> list[Surface]:

        a, b, width, height = rect
        rects = [
            (x, y, width, height)
            for y in range(b, self._sheet.get_height(), height)
            for x in range(a, self._sheet.get_width(), width)
        ]
        return self.images_at(rects, alpha, colorkey)


class SpriteKeeper:

    def __init__(self) -> None:
        self._sprites: dict[pathlib.Path, SpriteSheet] = {}

    def sprite(self, relative_path: str, alpha: bool) -> SpriteSheet:
        path = RESOURCE_DIR / relative_path
        try:
            return self._sprites[path]
        except KeyError:
            return self._sprites.setdefault(path, SpriteSheet(path, alpha))
