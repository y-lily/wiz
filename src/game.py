from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import ClassVar, Iterable

import pygame as pg
from lupa import LuaRuntime
from pygame import Rect, Surface

# TODO:
# from shared import pair
# import keybind, tuple_math
# from sprites import SpriteKeeper
from src import keybind, tuple_math
from src.adventure import (
    AdventureMap,
    AdventureMapBlueprint,
    Character,
    CharacterLoader,
    MapLoader,
    MapViewer,
)
from src.adventure.character_controller import CharacterType
from src.shared import pair
from src.sprites import SpriteKeeper
from src.ui import UI, WidgetLoader


class GameState(Enum):

    RUNNING = "running"
    FINISHED = "finished"
    PAUSED = "paused"


class Game:

    ZOOM_STEP: ClassVar = 0.25

    _collision_controller: CollisionController
    _trigger_controller: TriggerController
    _current_map: AdventureMap
    _hero: Character

    def __init__(self,
                 screen_size: pair,
                 map_loader: MapLoader,
                 sprite_keeper: SpriteKeeper,
                 ) -> None:

        self.state = GameState.FINISHED

        self._base_screen_size = screen_size

        screen = create_screen(screen_size)
        self._map_viewer = MapViewer(screen=screen)
        self._map_loader = map_loader
        self._character_loader = CharacterLoader(sprite_keeper)
        self._ui = UI(screen)
        self._widget_loader = WidgetLoader(self._ui,
                                           sprite_keeper)

    @property
    def load_widget(self) -> WidgetLoader:
        return self._widget_loader

    @property
    def viewer(self) -> MapViewer:
        return self._map_viewer

    def run(self) -> None:
        clock = pg.time.Clock()
        self.state = GameState.RUNNING

        while self.state != GameState.FINISHED:
            dt = clock.tick() / 1000.0
            self.update(dt)
            self.draw()
            pg.display.update()

    def draw(self) -> list[Rect]:
        self._map_viewer.center(self._hero.entity.rect.center)
        rects = self._map_viewer.draw()
        rects += self._ui.draw()
        return rects

    def update(self, dt: float) -> None:
        self._map_viewer.update_sprites(dt)
        self._collision_controller.update(dt)
        self._map_viewer.update_characters(dt)
        self._trigger_controller.update(dt)
        self._ui.update(dt)

        self._ui.handle_inputs()
        self.handle_inputs()

        for event in pg.event.get():
            if (event_type := event.type) == pg.QUIT:
                self.state = GameState.FINISHED
                return
            elif event_type == pg.VIDEORESIZE:
                self.set_screen((event.w, event.h))

    def handle_inputs(self) -> None:
        for event in pg.event.get(eventtype=pg.KEYDOWN):
            if (key := event.key) in keybind.ESCAPE:
                # TODO: Open the game menu here.
                self.state = GameState.FINISHED

            elif key in keybind.ZOOM_OUT:
                self._map_viewer.zoom -= self.ZOOM_STEP

            elif key in keybind.ZOOM_IN:
                self._map_viewer.zoom += self.ZOOM_STEP

            elif key in keybind.USE:
                self._trigger_controller.handle_use()

    def load_hero(self, path: Path) -> None:
        self._hero = self._character_loader.load(path, CharacterType.HERO)

    def load_map(self,
                 path: Path,
                 entry_point: str = "default",
                 ) -> None:

        assert hasattr(
            self, "_hero"), "Cannot load a map before loading a hero."

        new_map = self._map_loader.load(path)
        lua = LuaRuntime(unpack_returned_tuples=True)
        with open(path, "r") as map_file:
            map_table: AdventureMapBlueprint = lua.execute(map_file.read())

        spawn = map_table.entryPoints[entry_point]
        self._hero.entity.set_position(spawn["x"], spawn["y"])
        new_map.add_characters(self._hero)
        self._current_map = new_map

        self._load_controllers()

    def set_screen(self, screen_size: pair[int]) -> None:
        screen = create_screen(screen_size)
        self._map_viewer.set_screen(screen)
        self._ui.set_screen(screen)

        factor = tuple_math.div(screen_size,
                                self._base_screen_size)
        self._ui.scale(factor)

    def _load_controllers(self) -> None:
        self._map_viewer.set_map(current_map := self._current_map)
        self._map_viewer.add_sprites(self._hero.entity)

        if not hasattr(self, "_collision_controller"):
            self._collision_controller = CollisionController(current_map)
        else:
            self._collision_controller.set_map(current_map)

        if not hasattr(self, "_trigger_controller"):
            self._trigger_controller = TriggerController(current_map, self)
        else:
            self._trigger_controller.clear_tracked()
            self._trigger_controller.set_map(current_map)

        self._trigger_controller.start_tracking(self._hero)


class CollisionController:

    def __init__(self, adventure_map: AdventureMap) -> None:
        self._map = adventure_map

    def set_map(self, new_map: AdventureMap) -> None:
        self._map = new_map

    def update(self, dt: float) -> None:
        for character in self._map.characters:
            self._handle_collision(character, dt)

    def _handle_collision(self, character: Character, dt: float) -> None:
        if self._map.collision_zones.collides(character.entity):
            character.movement_controller.handle_collision(dt)


class TriggerController:

    def __init__(self,
                 adventure_map: AdventureMap,
                 game: Game,
                 tracked_characters: Iterable[Character] | None = None,
                 ) -> None:

        self._tracked_characters = set(
            tracked_characters) if tracked_characters is not None else set()
        self._map = adventure_map
        self._game = game

    def update(self, dt: float) -> None:
        for character in self._tracked_characters:
            self._handle_triggers(character, dt)

    def handle_use(self) -> None:
        for character in self._tracked_characters:
            for zone in character.entity.active_zones:
                zone.trigger.onUse(zone.trigger, character, self._game, zone)

    def start_tracking(self, character: Character) -> None:
        self._tracked_characters.add(character)

    def stop_tracking(self, character: Character) -> None:
        self._tracked_characters.remove(character)

    def clear_tracked(self) -> None:
        self._tracked_characters.clear()

    def set_map(self, new_map: AdventureMap) -> None:
        self._map = new_map

    def _handle_triggers(self, character: Character, dt: float) -> None:
        old = (entity := character.entity).active_zones
        new = set(self._map.trigger_zones.get_colliding_zones(entity))

        just_left = old.difference(new)
        old.difference_update(just_left)

        for zone in just_left:
            zone.trigger.onExit(zone.trigger, character, self._game, zone)

        just_entered = new.difference(old)
        old.update(just_entered)

        for zone in just_entered:
            zone.trigger.onEnter(zone.trigger, character, self._game, zone)


def create_screen(size: pair[int]) -> Surface:
    return pg.display.set_mode(size, pg.RESIZABLE)
