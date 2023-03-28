from __future__ import annotations

from typing import Any, Callable

import pygame as pg
from pygame.surface import Surface

from src.ui import UI, Widget, tuple_math
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
                 ui: UI,
                ) -> None:
        
        self._screen = screen
        self._last_screen_size = screen.get_size()
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
        shift = tuple_math.div(size, self._last_screen_size)
        shift = tuple_math.sub(shift, (1, 1))
        
        screen = create_screen(size)
        self._ui.set_screen(screen)
        self._ui.shift_scale(shift)

        self._last_screen_size = size
