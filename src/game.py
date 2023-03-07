from __future__ import annotations

from pathlib import Path

import pygame as pg
from lupa import LuaRuntime
from pygame.surface import Surface

from src.adventure import (
    AdventureMap,
    AdventureMapBlueprint,
    Character,
    CharacterLoader,
    MapLoader,
    MapViewer,
    keybind,
)
from src.sprites.sprite_keeper import SpriteKeeper
from src.ui import UI, WidgetLoader, tuple_math


class CollisionController:

    def __init__(self, map_: AdventureMap) -> None:
        self._map = map_

    def set_map(self, new_map: AdventureMap) -> None:
        self._map = new_map

    def update(self, dt: float) -> None:
        for character in self._map.characters:
            self._handle_collision(character, dt)

    def _handle_collision(self, character: Character, dt: float) -> None:
        if self._map.collision_zones.collides_sprite(character.entity):
            character.movement_controller.process_collision(dt)


class TriggerController:

    def __init__(self,
                 map_: AdventureMap,
                 game: 'Game',
                 tracked_characters: set[Character] | None = None,
                 ) -> None:

        self._tracked_characters = tracked_characters if tracked_characters else set()
        self._map = map_
        self._game = game

    def start_tracking(self, character: Character) -> None:
        self._tracked_characters.add(character)

    def stop_tracking(self, character: Character) -> None:
        self._tracked_characters.remove(character)

    def clear_tracking(self) -> None:
        self._tracked_characters.clear()

    def set_map(self, new_map: AdventureMap) -> None:
        self._map = new_map

    def update(self, dt: float) -> None:
        for character in self._tracked_characters:
            self._handle_triggers(character, dt)

    def invoke_use(self) -> None:
        for character in self._tracked_characters:
            for zone in character.entity.active_zones:
                zone.trigger.onUse(zone.trigger, character, self._game, zone)

    def _handle_triggers(self, character: Character, dt: float) -> None:
        old = character.entity.active_zones
        new = set(self._map.trigger_zones.get_all_colliding_zones(
            character.entity))

        just_left = old.difference(new)
        old.difference_update(just_left)
        for zone in just_left:
            zone.trigger.onExit(zone.trigger, character, self._game, zone)

        just_entered = new.difference(old)
        old.update(just_entered)
        for zone in just_entered:
            zone.trigger.onEnter(zone.trigger, character, self._game, zone)


class Game:

    ZOOM_STEP = 0.25

    def __init__(self,
                 screen_size: tuple[int, int],
                 map_loader: MapLoader,
                 sprite_keeper: SpriteKeeper,
                 ) -> None:

        self.state = "finished"

        screen = _create_screen(screen_size)
        # Used to calculate the scale value after screen resize.
        self._unscaled_screen_size = screen_size

        self._viewer = MapViewer(screen=screen)
        self._map_loader = map_loader
        self._char_loader = CharacterLoader(sprite_keeper)
        self._ui = UI(screen=screen)
        self._widget_loader = WidgetLoader(
            self._ui, sprite_keeper)

    # TODO
    # @classmethod
    # def from_savefile(): ...

    @property
    def viewer(self) -> MapViewer:
        return self._viewer

    @property
    def load_widget(self) -> WidgetLoader:
        return self._widget_loader

    def load_hero(self, path: Path) -> None:
        self.hero = self._char_loader.load(path, "HERO")

    def load_map(self,
                 path: Path,
                 entry_point: str = "default",
                 ) -> None:

        assert hasattr(self, "hero"), "The hero must be loaded before the map."
        new_map = self._map_loader.load(path)
        lua = LuaRuntime(unpack_returned_tuples=True)
        with open(path, "r") as file:
            table: AdventureMapBlueprint = lua.execute(file.read())

        spawn = table.entryPoints[entry_point]
        self.hero.entity.set_position(spawn["x"], spawn["y"])
        new_map.add_characters(self.hero)
        self.current_map = new_map
        self._load_controllers()

    def draw(self) -> None:
        self._viewer.center(self.hero.entity.rect.center)
        self._viewer.draw()
        self._ui.draw()

    def update(self, dt: float) -> None:
        self._viewer.update_sprites(dt)
        self.collision_controller.update(dt)
        self._viewer.update_characters(dt)
        self.trigger_controller.update(dt)
        self._ui.update(dt)

        # TODO: Move Viewer input handling into handle_inputs().
        # TODO: Consider breaking Viewer into multiple classes as it has too many responsibilities.

        # UI will take input events if there are widgets awaiting inputs.
        self._ui.handle_inputs()
        # Otherwise, the inputs are meant for the adventure map or to open the menu.
        self.handle_inputs()
        # Grab all events left and clear the event queue.
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.state = "finished"
                return
            elif event.type == pg.VIDEORESIZE:
                self.set_screen((event.w, event.h))

    def run(self) -> None:
        clock = pg.time.Clock()
        self.state = "running"

        while self.state != "finished":
            dt = clock.tick() / 1000.0
            self.update(dt)
            self.draw()
            pg.display.update()

    def set_screen(self, screen_size: tuple[int, int]) -> None:
        screen = _create_screen(screen_size)
        self._viewer.set_screen(screen)
        self._ui.set_screen(screen)

        scale_factor = tuple_math.div(screen_size,
                                         self._unscaled_screen_size)
        self._ui.scale(scale_factor)

    def _load_controllers(self) -> None:
        self._viewer.set_map(new_map=self.current_map)
        self._viewer.add_sprites(self.hero.entity)
        if not hasattr(self, "collision_controller"):
            self.collision_controller = CollisionController(self.current_map)
        else:
            self.collision_controller.set_map(self.current_map)
        if not hasattr(self, "trigger_controller"):
            self.trigger_controller = TriggerController(self.current_map, self)
        else:
            self.trigger_controller.clear_tracking()
            self.trigger_controller.set_map(self.current_map)
        self.trigger_controller.start_tracking(self.hero)

    def handle_inputs(self) -> None:
        for event in pg.event.get(eventtype=pg.KEYDOWN):
            if event.key in (keybind.ESCAPE):
                # TODO: Open the game menu here.
                self.state = "finished"
            elif event.key in (keybind.ZOOM_OUT):
                self._viewer.zoom -= self.ZOOM_STEP
            elif event.key in (keybind.ZOOM_IN):
                self._viewer.zoom += self.ZOOM_STEP
            elif event.key in (keybind.USE):
                self.trigger_controller.invoke_use()


def _create_screen(size: tuple[int, int]) -> Surface:
    screen = pg.display.set_mode(size, pg.RESIZABLE)
    return screen
