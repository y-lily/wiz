from __future__ import annotations

import pygame as pg
import tuple_math
from pygame import Surface
from tuple_math import pair

from src.ui import UI


def create_screen(size: pair[int]) -> Surface:
    return pg.display.set_mode(size, pg.RESIZABLE)


class MockApp:

    _DEFAULT_BG_COLOR = (100, 0, 0)

    def __init__(self,
                 screen: Surface,
                 ui: UI,
                 ) -> None:

        self._screen = screen
        # self._last_screen_size = screen.get_size()
        self._base_size = screen.get_size()
        self._ui = ui

    def run(self) -> None:
        clock = pg.time.Clock()
        self.state = "running"

        while self.state == "running":
            dt = clock.tick() / 1000.0

            self._screen.fill(self._DEFAULT_BG_COLOR)
            self.update(dt)
            self.draw()
            self.handle_events()
            pg.display.update()

    def update(self, dt: float) -> None:
        self._ui.update(dt)

    def draw(self) -> None:
        self._ui.draw()

    def handle_events(self) -> None:
        self._ui.handle_inputs()

        for event in pg.event.get():
            if any([event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE,
                    event.type == pg.QUIT]):
                self.state = "finished"
            elif event.type == pg.VIDEORESIZE:
                self.set_screen((event.w, event.h))

    def set_screen(self, size: pair[int]) -> None:

        shift = tuple_math.div(size, self._base_size)

        screen = create_screen(size)
        self._ui.set_screen(screen)
        self._ui.scale(shift)
