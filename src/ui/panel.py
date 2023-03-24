from typing import Sequence

import pygame as pg
from pygame.surface import Surface

from ..sprites import SpriteKeeper
from . import tuple_math
from .shared import pair


class Panel(Surface):
    """A surface with a border built from parts.
    Like any other surface, it is not attached to a specific area of the screen."""

    def __init__(self,
                 size: pair[int],
                 parts: list[Surface],
                 flags: int = 0,
                 ) -> None:

        super().__init__(size, flags)
        if len(parts) != 9:
            raise ValueError("Received wrong number of parts.")

        if not _of_equal_size(parts):
            raise ValueError("Received parts of different size.")

        topleft, top, topright, left, center, right, bottomleft, bottom, bottomright = parts
        part_size = topleft.get_size()
        shrunk_size = tuple_math.mod_round_down(size, part_size)

        surf = Surface(shrunk_size, flags)
        center_start = part_size
        center_end = tuple_math.sub(shrunk_size, part_size)

        def blit_line(start: Surface, mid: Surface, end: Surface, y: int) -> None:
            surf.blit(start, (0, y))
            surf.blits([(mid, (x, y))
                        for x in range(center_start[0], center_end[0], part_size[0])])
            surf.blit(end, (center_end[0], y))

        blit_line(topleft, top, topright, 0)
        for y in range(center_start[1], center_end[1], part_size[1]):
            blit_line(left, center, right, y)
        blit_line(bottomleft, bottom, bottomright, center_end[1])

        pg.transform.smoothscale(surf, size, self)


class PanelBuilder:

    def __init__(self,
                 sprite_keeper: SpriteKeeper,
                 default_path: str | None = None,
                 ) -> None:

        self._sprite_keeper = sprite_keeper
        self._default_path = default_path

    def build_panel(self,
                    size: pair[int],
                    path: str | None = None,
                    alpha: bool = False,
                    ) -> Panel:

        path = path if path is not None else self._default_path
        if path is None:
            raise TypeError(
                "Cannot find the image, neither the path nor the default path were given.")

        atlas = self._sprite_keeper.sprite(path, alpha)
        part_size = tuple_math.floor_div(atlas.size, (3, 3))
        parts = atlas.split(part_size)
        flags = pg.SRCALPHA if alpha else 0
        return Panel(size, parts, flags)


def _of_equal_size(surfaces: Sequence[Surface]) -> bool:
    sample_size = surfaces[0].get_size()
    return all(surf.get_size() == sample_size for surf in surfaces[1:])
