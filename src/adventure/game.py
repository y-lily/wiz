from __future__ import annotations

from typing import Literal

import pygame
import pytmx
from pygame.surface import Surface

from . import shared
from .adventure_map import AdventureMap
from .character import Hero
from .lua_defs import LuaMapTable
from .map_controller import CollisionController, MapViewer, TriggerController
from .shared import RESOURCE_DIR, Controller, Path
from .sprite_sheet import SpriteKeeper

try:
    from typing import Self
except ImportError:
    from typing_extensions import Self


class Game:

    _sprite_keeper = SpriteKeeper()

    def __init__(self,
                 start_map: AdventureMap,
                 hero: Hero,
                 screen: Surface,
                 ) -> None:

        self.running = False
        self.screen = screen
        self.hero = hero

        self.load_map(start_map)

        # TODO: Remove it.
        self.viewer.hide_layers("roof")

    @classmethod
    def from_file(cls,
                  path: Path,
                  screen: Surface,
                  ) -> Self:

        table: LuaMapTable = shared.load_table(path)
        tmx = pytmx.load_pygame(RESOURCE_DIR / table.tmx)
        map_ = AdventureMap(tmx)

        assert not map_.loaded, "Cannot load twice."
        loader = table.onLoad
        for call in loader.values():
            call(table, map_)
        hero = map_.spawn_char_call(
            "hero", table=table, char_type=Hero)
        map_.loaded = True

        return cls(map_, hero, screen)

    # TODO
    # @classmethod
    # def from_savefile(): ...

    def draw(self) -> None:
        self.viewer.center(self.hero.entity.rect.center)
        self.viewer.draw()

    def update(self, dt: float) -> None:
        for controller in self.controllers:
            controller.update(dt)

    def run(self) -> None:
        clock = pygame.time.Clock()
        self.running = True

        while self.running:
            dt = clock.tick() / 1000.0
            self._process_pygame_events()
            self._process_pressed_keys()
            self.update(dt)
            self.draw()
            pygame.display.update()

    def load_map(self, new_map: AdventureMap) -> None:
        self.current_map = new_map
        self.viewer = MapViewer(new_map, self.screen)
        self.viewer.add_characters(self.hero)
        self.collision_controller = CollisionController(self.viewer)
        self.trigger_controller = TriggerController(self.viewer)
        self.trigger_controller.start_tracking(self.hero)

        self.controllers: list[Controller] = [self.viewer,
                                              self.collision_controller,
                                              self.trigger_controller,
                                              ]

    def _process_pygame_events(self) -> None:
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                self.running = False
                return

            elif event.type == pygame.KEYDOWN:
                self._process_input(event.key)

            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h),
                                                 pygame.RESIZABLE)
                self.viewer.set_screen(screen)

    def _process_input(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.running = False

        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.viewer.zoom -= 0.25

        elif key in (pygame.K_EQUALS, pygame.K_KP_PLUS):
            self.viewer.zoom += 0.25

        elif key == pygame.K_SPACE:
            self.trigger_controller.invoke_use()

    def _process_pressed_keys(self) -> None:
        pressed = pygame.key.get_pressed()

        if pressed[pygame.K_UP]:
            y: Literal[-1, 0, 1] = -1
        elif pressed[pygame.K_DOWN]:
            y = 1
        else:
            y = 0

        if pressed[pygame.K_LEFT]:
            x: Literal[-1, 0, 1] = -1
        elif pressed[pygame.K_RIGHT]:
            x = 1
        else:
            x = 0

        self.hero.movement_controller.process_player_move_command(x, y)

    # def _spawn_npc_call(self, name: str, )
