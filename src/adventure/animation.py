from __future__ import annotations

import pathlib
from typing import Optional, Type, TypeVar
from xml.etree import ElementTree

import pygame
from pygame.surface import Surface

from src.adventure.shared import Direction, Path
from src.adventure.sprite_sheet import SpriteSheet


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

    @property
    def current_frame(self) -> int:
        return int(self._current_frame)

    @current_frame.setter
    def current_frame(self, new_value: int) -> None:
        self._current_frame = new_value

    def update(self, dt: float) -> None:
        self._current_frame += self._frame_rate * dt
        if self._current_frame >= len(self._frames[self.state]):
            self._current_frame = 0

    def get_image(self) -> Surface:
        return self._frames[self.state][self.current_frame]

    @staticmethod
    def from_xml_data(data: ElementTree.Element,
                      res_dir: Path,
                      atlas: Optional[SpriteSheet] = None,
                      ) -> Animation:

        res_dir = pathlib.Path(res_dir)
        alpha = _get_boolean(data.attrib, "alpha", default=False)
        atlas = atlas if atlas is not None else SpriteSheet(
            res_dir / data.attrib["source"], alpha=alpha)
        width = int(data.attrib["framewidth"])
        height = int(data.attrib["frameheight"])
        frame_rate = int(data.attrib["framerate"])
        colorkey = _get_tuple(data.attrib, "colorkey", target_type=int)
        initial_frame = int(data.get("initial_frame", 0))
        initial_state = _get_converted(data.attrib,
                                       "initial_state",
                                       default=None,
                                       target_type=Direction)

        sprites = atlas.split((0, 0, width, height),
                              alpha=alpha,
                              colorkey=colorkey)

        frames: dict[Direction, list[Surface]] = {}

        for direction_data in data:
            frames[Direction(direction_data.tag)] = [
                sprites[i] for i in _get_tuple(direction_data.attrib, "frames", target_type=int)]

        frames |= _get_inverted_right_to_left(frames)

        return Animation(frames=frames,
                         frame_rate=frame_rate,
                         initial_state=initial_state,
                         initial_frame=initial_frame)


T = TypeVar("T")


def _get_converted(data: dict[str, str],
                   field_name: str,
                   default: Optional[T] = None,
                   target_type: Type[T] = str,
                   ) -> Optional[T]:

    raw = data.get(field_name, default)

    if raw == default:
        return default

    return target_type(raw)


def _get_boolean(data: dict[str, str],
                 field_name: str,
                 default: Optional[bool] = False,
                 ) -> Optional[bool]:
    # Requires special attention.

    raw = data.get(field_name, default)

    if raw == default:
        return default

    if raw.lower() == "true":
        return True
    elif raw.lower() == "false":
        return False
    else:
        return default


def _get_tuple(data: dict[str, str],
               field_name: str,
               default: Optional[T] = None,
               target_type: Type[T] = str,
               sep: str = ", ",
               ) -> Optional[tuple[T, ...]]:

    unparsed = data.get(field_name, default)

    if unparsed == default:
        return default

    return tuple(target_type(x) for x in unparsed.split(sep))


def _get_inverted_right_to_left(frames: dict[Direction, list[Surface]]) -> dict[Direction, list[Surface]]:
    inverted_frames = {}

    supported_directions = {Direction.DOWNRIGHT: Direction.DOWNLEFT,
                            Direction.RIGHT: Direction.LEFT,
                            Direction.UPRIGHT: Direction.UPLEFT}

    for direction in frames.keys():
        try:
            inverted_direction = supported_directions[direction]
        except KeyError:
            continue

        inverted_frames[inverted_direction] = [
            pygame.transform.flip(frame, True, False) for frame in frames[direction]]

    return inverted_frames
