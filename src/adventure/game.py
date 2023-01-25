from __future__ import annotations

from typing import Literal

import pygame
import pytmx
from lupa import LuaRuntime
from pygame.surface import Surface

from .adventure_map import AdventureMap
from .character import Hero
from .lua_defs import LuaMapTable
from .map_controller import CollisionController, MapViewer, TriggerController
from .shared import RESOURCE_DIR, Controller, Path


class Game:

    def __init__(self,
                 screen: Surface,
                 map_path: Path,
                 hero_path: Path | None = None,
                 entry_point: str = "default",
                 ) -> None:

        self.running = False
        self.screen = screen

        lua = LuaRuntime(unpack_returned_tuples=True)
        map_table: LuaMapTable = lua.execute(open(map_path, "r").read())

        if hero_path is None:
            hero_table = map_table
        else:
            hero_table = lua.execute(open(hero_path, "r").read())

        tmx = pytmx.load_pygame(RESOURCE_DIR / map_table.tmx)
        new_map = AdventureMap(tmx)

        self.hero = new_map.spawn_char_call(
            "hero", table=hero_table, char_type=Hero)
        self.load_map(new_map, lua, map_table, entry_point)

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

    def load_map_from_file(self,
                           path: Path,
                           entry_point: str = "default",
                           ) -> None:

        lua = LuaRuntime(unpack_returned_tuples=True)
        with open(path, "r") as file:
            table: LuaMapTable = lua.execute(file.read())

        tmx = pytmx.load_pygame(RESOURCE_DIR / table.tmx)
        map_ = AdventureMap(tmx)
        self.load_map(new_map=map_, lua=lua, table=table,
                      entry_point=entry_point)

    def load_map(self,
                 new_map: AdventureMap,
                 lua: LuaRuntime,
                 table: LuaMapTable,
                 entry_point: str = "default",
                 ) -> None:

        assert hasattr(
            self, "hero"), "Cannot load a map when the hero does not exist."
        assert not new_map.loaded, "Cannot load twice."

        loader = table.onLoad
        for call in loader.values():
            call(table, new_map)
        new_map.loaded = True

        spawn = table.entryPoints[entry_point]
        self.hero.entity.set_position(spawn["x"], spawn["y"])
        new_map.add_characters(self.hero)
        self.current_map = new_map
        self._load_controllers(lua)

    def _load_controllers(self, lua: LuaRuntime) -> None:
        self.controllers: list[Controller] = []

        self.viewer = MapViewer(self.current_map, self.screen, lua)
        self.viewer.add_sprites(self.hero.entity)
        collision_controller = CollisionController(self.viewer)
        # self.trigger_controller = TriggerController(self.viewer)
        self.trigger_controller = TriggerController(self.viewer, self)
        self.trigger_controller.start_tracking(self.hero)

        self.controllers.append(self.viewer)
        self.controllers.append(collision_controller)
        self.controllers.append(self.trigger_controller)

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
