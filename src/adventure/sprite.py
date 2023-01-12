import pathlib
from typing import Any, NoReturn, Sequence, overload
import pygame
from lib.assert_never import assert_never


COLLISION_BOX_WIDTH_RATIO = 0.35
COLLISION_BOX_HEIGHT_RATIO = 0.25


class Sprite(pygame.sprite.Sprite):

    @overload
    def __init__(self,
                 *,
                 image: pygame.surface.Surface,
                 position: tuple[int, int] | None) -> None: ...

    @overload
    def __init__(self,
                 *,
                 image_path: str | pathlib.Path,
                 position: tuple[int, int] | None) -> None: ...

    def __init__(self,
                 *args: NoReturn,
                 image: pygame.surface.Surface | None = None,
                 image_path: str | pathlib.Path | None = None,
                 position: tuple[int, int] | None = None) -> None:
        super().__init__()

        if image is not None:
            self.image = image

        elif image_path is not None:
            self.image = pygame.image.load(image_path)

        else:
            assert_never(*args)

        self.rect: pygame.rect.Rect = self.image.get_rect()

        if position is not None:
            self.set_position(position)

    def set_position(self, new_position: tuple[int, int]) -> None:
        self.rect.topleft = new_position


class MovingSprite(Sprite):

    @overload
    def __init__(self,
                 *,
                 image: pygame.surface.Surface,
                 movement_speed: int) -> None: ...

    @overload
    def __init__(self,
                 *,
                 image_path: str | pathlib.Path,
                 movement_speed: int) -> None: ...

    def __init__(self,
                 movement_speed: int,
                 *args: Any,
                 **kwargs: Any,
                 ) -> None:
        super().__init__(*args, **kwargs)

        self.movement_speed = movement_speed
        self._velocity = [0.0, 0.0]
        self._position: list[float] = list(self.rect.topleft)
        self._last_stable_ground = list(self._position)
        self._collision_box: pygame.rect.Rect = pygame.Rect(
            0,
            0,
            self.rect.width * COLLISION_BOX_WIDTH_RATIO,
            self.rect.height * COLLISION_BOX_HEIGHT_RATIO)

    @property
    def velocity(self) -> list[float]:
        return self._velocity

    def find_collision(self, collision_list: Sequence[pygame.rect.Rect]) -> int:
        return self._collision_box.collidelist(collision_list)

    def return_to_last_stable_ground(self) -> None:
        self._position = list(self._last_stable_ground)
        self.rect.topleft = int(self._position[0]), int(self._position[1])
        self._collision_box.midbottom = self.rect.midbottom

    def set_position(self, new_position: tuple[int, int]) -> None:
        super().set_position(new_position)
        self._position = list(self.rect.topleft)
        self._collision_box.midbottom = self.rect.midbottom

    def update(self, dt: float) -> None:
        self._last_stable_ground = list(self._position)
        self._position[0] += self._velocity[0] * dt
        self._position[1] += self._velocity[1] * dt
        self.rect.topleft = (
            int(self._position[0]),
            int(self._position[1]))
        self._collision_box.midbottom = self.rect.midbottom
