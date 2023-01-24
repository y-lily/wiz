from __future__ import annotations

from contextlib import suppress
from typing import Optional

import pygame
from pygame.surface import Surface

from . import shared
from .lua_defs import LuaEntityTable
from .shared import Direction
from .sprite_sheet import SpriteSheet

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


class Animation:

    def __init__(self,
                 frames: dict[Direction, list[Surface]],
                 frame_rate: int,
                 initial_state: Optional[Direction] = None,
                 initial_frame: int = 0,
                 ) -> None:

        self._frames = frames
        self._frame_rate = frame_rate
        self.state = initial_state if initial_state is not None else Direction.DOWN
        self._current_frame: float = initial_frame
        self._default_image = self.get_image()

    @property
    def current_frame(self) -> int:
        return int(self._current_frame)

    @current_frame.setter
    def current_frame(self, new_value: int) -> None:
        self._current_frame = new_value

    def __getitem__(self, direction: Direction) -> list[Surface]:
        return self._frames[direction]

    def update(self, dt: float) -> None:
        self._current_frame += self._frame_rate * dt
        if self._current_frame >= len(self._frames[self.state]):
            self._current_frame = 0

    def get_image(self) -> Surface:
        with suppress(KeyError):
            return self._frames[self.state][self.current_frame]
        return self._default_image

    @classmethod
    def from_table(cls,
                   table: LuaEntityTable,
                   atlas: SpriteSheet,
                   ) -> dict[str, Self]:

        sprites = atlas.split(
            (0, 0, table.framewidth, table.frameheight), alpha=table.alpha)
        framerate = table.framerate

        animations = {}
        for animation, animation_data in table.animations.items():
            frames = {}
            for direction, frames_data in animation_data.items():
                frames[Direction(direction)] = [
                    sprites[i] for i in frames_data.values()]

            if table.flip == "right-left":
                frames |= _flipped_left(frames)
            elif table.flip is None:
                pass
            else:
                shared.assert_never(table.flip)

            animations[animation] = Animation(frames=frames,
                                              frame_rate=framerate)

        return animations


def _flipped_left(source: dict[Direction, list[Surface]]) -> dict[Direction, list[Surface]]:
    flipped: dict[Direction, list[Surface]] = {}

    supported_directions = {Direction.DOWNRIGHT: Direction.DOWNLEFT,
                            Direction.RIGHT: Direction.LEFT,
                            Direction.UPRIGHT: Direction.UPLEFT}

    for direction, frames in source.items():
        try:
            flipped_direction = supported_directions[direction]
        except KeyError:
            continue

        flipped[flipped_direction] = [
            pygame.transform.flip(frame, True, False) for frame in frames]

    return flipped
