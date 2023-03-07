from contextlib import suppress
from typing import TypeVar

from pygame.event import Event
from pygame.surface import Surface

T = TypeVar("T", bound=object)


class Animation:

    def __init__(self,
                 frames: dict[T, list[Surface]],
                 frame_rate: int,
                 initial_state: T,
                 initial_frame: int = 0,
                 ) -> None:

        self._frames = frames
        self._frame_rate = frame_rate
        self.state = initial_state
        self._current_frame: float = initial_frame
        self._default_image = self.get_image()

    @property
    def current_frame(self) -> int:
        return int(self._current_frame)

    @current_frame.setter
    def current_frame(self, new_value: int) -> None:
        self._current_frame = new_value

    def __getitem__(self, key: T) -> list[Surface]:
        return self._frames[key]

    def update(self, dt: float) -> None:
        self._current_frame += self._frame_rate * dt
        if self._current_frame >= len(self._frames[self.state]):
            self._current_frame = 0

    def get_image(self) -> Surface:
        with suppress(KeyError):
            return self._frames[self.state][self.current_frame]
        return self._default_image
