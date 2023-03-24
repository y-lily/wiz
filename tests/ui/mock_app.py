from __future__ import annotations

from typing import Any, Callable

import pygame as pg
from pygame.surface import Surface

from src.ui import Widget, tuple_math
from src.ui.shared import pair


class MockTrigger:

    def __init__(self,
                 on_kill: Callable[[MockTrigger, Widget], None] | None = None,
                 on_send: Callable[[MockTrigger, Widget, Any], None] | None = None,
                 on_use: Callable[[MockTrigger, Widget], None] | None = None,
                 ) -> None:
        
        self._on_kill = on_kill if on_kill is not None else _no_op
        self._on_send = on_send if on_send is not None else _no_op
        self._on_use = on_use if on_use is not None else _no_op

    def onKill(self, widget: Widget) -> None:
        self._on_kill(self, widget)

    def onUse(self, widget: Widget) -> None:
        self._on_use(self, widget)

    def onSend(self, widget: Widget, data_sent: Any) -> None:
        self._on_send(self, widget, data_sent)

def create_screen(size: pair[int]) -> Surface:
    return pg.display.set_mode(size, pg.RESIZABLE)

def _no_op(*args: Any, **kwargs: Any) -> None:
    return None
    

class MockApp:

    _DEFAULT_BG_COLOR = (100, 0, 0)

    def __init__(self,
                 screen: Surface,
                 *widgets: Widget,
                 timer: float = 10,
                ) -> None:
        
        self._screen = screen
        self._DEFAULT_SCREEN_SIZE = screen.get_size()
        self._widgets = [*widgets]
        self._time_left = timer

    def run(self) -> None:
        clock = pg.time.Clock()
        self.state = "running"

        while self.state == "running":
            dt = clock.tick() / 1000.0
            self._time_left -= dt

            if self._time_left <= 0:
                self.state = "finished"
                return

            self._screen.fill(self._DEFAULT_BG_COLOR)
            self.update(dt)
            self.draw()
            self.handle_events()
            pg.display.update()

    def update(self, dt: float) -> None:
        for widget in self._widgets:
            widget.update(dt)

    def draw(self) -> None:
        for widget in self._widgets:
            widget.draw(self._screen)

    def handle_events(self) -> None:
        try:
            top = self._widgets[-1]
        except IndexError:
            pass
        else:
            top.handle_inputs()

        for event in pg.event.get():
            if any([event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE,
                    event.type == pg.QUIT]):
                self.state = "finished"
            elif event.type == pg.VIDEORESIZE:
                self.set_screen((event.w, event.h))

    def set_screen(self, size: pair[int]) -> None:
        self._screen = create_screen(size)
        scale_factor = tuple_math.div(size, self._DEFAULT_SCREEN_SIZE)

        for widget in self._widgets:
            widget.scale(scale_factor)
