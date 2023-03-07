from pathlib import Path
from typing import Callable, Iterable

import pytmx
from lupa import LuaRuntime
from pygame.rect import Rect

from ..sprites import SpriteKeeper
from .adventure_map import (
    AdventureMap,
    CharacterTriggerZone,
    TriggerZone,
    Zone,
    ZoneList,
)
from .blueprint import AdventureMapBlueprint

COLLISION_LAYER = "collisions"
TRIGGER_LAYER = "interaction_zones"
DEFAULT_LAYER = "sprites"
TRIGGER_PROPERTY = "trigger"


class MapLoader:

    def __init__(self, resource_dir: Path) -> None:
        self.resource_dir = resource_dir
        # NOTE: A new sprite keeper is created for each map although it might be better to share one.

    def load(self, map_path: Path) -> AdventureMap:
        lua = LuaRuntime(unpack_returned_tuples=True)
        with open(map_path, "r") as file:
            map_def: AdventureMapBlueprint = lua.execute(file.read())
        tmx = pytmx.load_pygame(self.resource_dir / map_def.tmx)
        sprite_keeper = SpriteKeeper(self.resource_dir)

        new_map = AdventureMap(tmx=tmx, sprite_keeper=sprite_keeper)

        return self._setup_map(new_map=new_map, lua=lua, on_load=map_def.onLoad.values())

    def _setup_map(self,
                   new_map: AdventureMap,
                   lua: LuaRuntime,
                   on_load: Iterable[Callable[[AdventureMap], None]],
                   ) -> AdventureMap:

        assert not new_map.loaded, "Cannot load a map twice."
        # Perform NPC loading and any other onLoad calls.
        for call in on_load:
            call(new_map)
        new_map.loaded = True

        # Set the default layer where the sprites will be loaded.
        new_map.default_layer = new_map.get_layer_index(DEFAULT_LAYER)

        collision_zones: ZoneList[Zone] = ZoneList()
        for obj in new_map.get_layer(COLLISION_LAYER):
            rect = Rect(obj.x, obj.y, obj.width, obj.height)
            collision_zones.append(Zone(rect=rect))
        new_map.set_collision_zones(collision_zones)

        trigger_zones: ZoneList[TriggerZone] = ZoneList()
        for obj in new_map.get_layer(TRIGGER_LAYER):
            rect = Rect(obj.x, obj.y, obj.width, obj.height)
            trigger = lua.execute(obj.properties[TRIGGER_PROPERTY])
            trigger_zones.append(TriggerZone(rect=rect, trigger=trigger))
        # Loaded NPCs are also treated as walking trigger zones.
        for char in new_map.characters:
            # NOTE: You can use the entire char rect as a trigger rect instead,
            # or even create some sort of a trigger rect.
            rect = char.entity.collision_box
            trigger = char.trigger
            trigger_zones.append(CharacterTriggerZone(character=char))
        new_map.set_trigger_zones(trigger_zones)

        return new_map
