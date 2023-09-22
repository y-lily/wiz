from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

import pygame as pg
import tuple_math
from pygame import Rect, Surface
from pygame.sprite import Sprite
from tuple_math import pair
from typing_extensions import override

from src.shared import Direction
from src.sprites import Animation

if TYPE_CHECKING:
    from .adventure_map import TriggerZone

from .blueprint import Position

COLLISION_BOX_WIDTH_RATIO = 0.25
COLLISION_BOX_HEIGHT_RATIO = 0.25


MOVEMENT_SPEED_CAP = 1500


class Entity(Sprite):

    _position: list[float]

    def __init__(self,
                 *,
                 image: Surface,
                 position: Position | None = None,
                 ) -> None:

        super().__init__()
        self.image = image
        self.rect = image.get_rect()
        self._position = [position["x"],
                          position["y"]] if position is not None else [0, 0]
        self._match_position()

    @property
    def position(self) -> pair[int]:
        return tuple_math.intify(self._position)

    def set_position(self, x: int, y: int) -> None:
        self._position = [x, y]
        self._match_position()

    def update(self, dt: float) -> None:
        pass

    def _match_position(self) -> None:
        self.rect.topleft = self.position


class MovingEntity(Entity):

    def __init__(self,
                 *args: object,
                 animations: dict[str, Animation],
                 movement_speed: float,
                 state: str = "initial",
                 face_direction: str | Direction,
                 frame: int = 0,
                 image: Surface | None = None,
                 position: Position | None = None,
                 **kwargs: object,
                 ) -> None:

        self.state = state
        self._face_direction = Direction(face_direction)

        if image is not None:
            self._default_image = image
        else:
            try:
                self._default_image = animations[self.state][self._face_direction][frame]
            except KeyError:
                self._default_image = next(
                    animation for animation in animations.values())[self._face_direction][frame]

        self.mask = pg.mask.from_surface(self._default_image)
        width, height = self.mask.get_size()
        self._collision_box = Rect(0,
                                   0,
                                   width * COLLISION_BOX_WIDTH_RATIO,
                                   height * COLLISION_BOX_HEIGHT_RATIO)

        super().__init__(*args,
                         image=self._default_image,
                         position=position,
                         **kwargs,
                         )

        self._last_stable_ground = list(self._position)

        self._animations = animations
        self._movement_speed = movement_speed
        self._ensure_valid_ms()
        self._velocity: list[float] = [0, 0]

        self._active_zones: set[TriggerZone] = set()

    @property
    def animations(self) -> dict[str, Animation]:
        return self._animations

    @property
    def active_zones(self) -> set[TriggerZone]:
        return self._active_zones

    @property
    def collision_box(self) -> Rect:
        return self._collision_box

    @property
    def velocity(self) -> list[float]:
        return self._velocity

    @property
    def face_direction(self) -> Direction:
        return self._face_direction

    @face_direction.setter
    def face_direction(self, new: str | Direction) -> None:
        self._face_direction = Direction(new)

    @property
    def movement_speed(self) -> float:
        return self._movement_speed

    @movement_speed.setter
    def movement_speed(self, new_value: float) -> None:
        self._movement_speed = new_value
        self._ensure_valid_ms()

    def find_collision(self, zones: Sequence[Rect]) -> int:
        return self._collision_box.collidelist(zones)

    def find_all_collisions(self, zones: Sequence[Rect]) -> list[int]:
        return self._collision_box.collidelistall(zones)

    def to_last_stable_ground(self, dt: float) -> None:
        self._position = list(self._last_stable_ground)
        self._match_position()

    def update(self, dt: float) -> None:
        self._last_stable_ground = list(self._position)
        self._position[0] += self._velocity[0] * dt
        self._position[1] += self._velocity[1] * dt
        self._match_position()

    def _ensure_valid_ms(self) -> None:
        if self._movement_speed > MOVEMENT_SPEED_CAP:
            print(
                f"Warning, movement speed = {self._movement_speed} has been reduced to {MOVEMENT_SPEED_CAP}!")
            self._movement_speed = MOVEMENT_SPEED_CAP

    @override
    def _match_position(self) -> None:
        super()._match_position()
        self._collision_box.midbottom = self.rect.midbottom
