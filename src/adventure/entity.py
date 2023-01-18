from __future__ import annotations

from typing import Optional, Sequence

from pygame.rect import Rect
from pygame.sprite import Sprite
from pygame.surface import Surface
from typing_extensions import override

from src.adventure.animation import Animation
from src.adventure.trigger import Trigger

COLLISION_BOX_WIDTH_RATIO = 0.35
COLLISION_BOX_HEIGHT_RATIO = 0.25


class Entity(Sprite):

    def __init__(self,
                 image: Surface,
                 position: Optional[tuple[float, float]] = None,
                 ) -> None:

        super().__init__()
        self.image = image
        self.rect: Rect = image.get_rect()
        self._position = list(
            position) if position is not None else list(self.rect.topleft)

    def set_position(self, x: int, y: int) -> None:
        self._position = [x, y]

    def update(self, dt: float) -> None:
        self._match_position()

    def _match_position(self) -> None:
        self.rect.topleft = (int(self._position[0]),
                             int(self._position[1]))


class MovingEntity(Entity):

    def __init__(self,
                 idle_animation: Animation,
                 walk_animation: Animation,
                 movement_speed: float,
                 image: Optional[Surface] = None,
                 position: Optional[tuple[float, float]] = None,
                 ) -> None:

        image = image if image is not None else idle_animation.get_image()
        super().__init__(image, position)
        self._last_stable_ground = list(self._position)

        self._collision_box = Rect(0,
                                   0,
                                   self.rect.width * COLLISION_BOX_WIDTH_RATIO,
                                   self.rect.height * COLLISION_BOX_HEIGHT_RATIO)

        self._idle_animation = idle_animation
        self._walk_animation = walk_animation

        self._movement_speed = movement_speed
        self._velocity: list[float] = [0, 0]
        self.movement_state = "idle"
        self.face_direction = "down"

        self._zonal_triggers: dict[int, Trigger] = {}

    @property
    def idle_animation(self) -> Animation:
        return self._idle_animation

    @property
    def zonal_triggers(self) -> dict[int, Trigger]:
        return self._zonal_triggers

    @property
    def walk_animation(self) -> Animation:
        return self._walk_animation

    @property
    def velocity(self) -> list[float]:
        return self._velocity

    @property
    def movement_speed(self) -> float:
        return self._movement_speed

    def find_collision(self, zones: Sequence[Rect]) -> int:
        return self._collision_box.collidelist(zones)

    def find_all_collisions(self, zones: Sequence[Rect]) -> list[int]:
        return self._collision_box.collidelistall(zones)

    def to_last_stable_ground(self) -> None:
        self._position = list(self._last_stable_ground)
        self._match_position()

    def update(self, dt: float) -> None:
        self._last_stable_ground = list(self._position)
        self._position[0] += self._velocity[0] * dt
        self._position[1] += self._velocity[1] * dt
        self._match_position()

    @override
    def _match_position(self) -> None:
        super()._match_position()
        self._collision_box.midbottom = self.rect.midbottom
