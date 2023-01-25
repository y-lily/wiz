from typing import Any, Optional

from lupa import LuaRuntime
from pygame.rect import Rect
from pygame.sprite import Sprite
from pygame.surface import Surface
from pyscroll import BufferedRenderer, PyscrollGroup
from pyscroll.data import TiledMapData
from pytmx import TiledElement, TiledObject

from .adventure_map import AdventureMap, TriggerZone, Zone, ZoneList
from .character import Character
from .entity import Entity
from .shared import Controller


class MapViewer(Controller):

    _scroller: BufferedRenderer
    _group: PyscrollGroup
    _trigger_zones: ZoneList[TriggerZone]
    _collision_zones: ZoneList[Zone]
    _map: AdventureMap
    _hidden_layers: dict[str, list[Entity]]

    def __init__(self,
                 new_map: AdventureMap,
                 screen: Surface,
                 lua: LuaRuntime
                 ) -> None:

        self._screen = screen
        self.lua = lua
        self.replace_map(new_map)  # Load scroller, group, zones, sprites.

    @property
    def collision_zones(self) -> ZoneList[Zone]:
        return self._collision_zones

    @property
    def trigger_zones(self) -> ZoneList[TriggerZone]:
        return self._trigger_zones

    @property
    def zoom(self) -> float:
        return float(self._scroller.zoom)

    @zoom.setter
    def zoom(self, new_value: float) -> None:
        self._scroller.zoom = new_value

    @property
    def characters(self) -> tuple[Character, ...]:
        return self._map.characters

    # @property
    # def sprites(self) -> list[Sprite]:
    #     return self._group.sprites()

    def add_sprites(self, *sprites: Sprite, layer: Optional[int] = None) -> None:
        self._group.add(sprites, layer=layer)

    def remove_sprites(self, *sprites: Sprite) -> None:
        self._group.remove(sprites)

    def center(self, pixel: tuple[int, int]) -> None:
        self._group.center(pixel)

    def draw(self) -> None:
        self._group.draw(self._screen)

    def set_screen(self, new_screen: Surface) -> None:
        self._screen = new_screen
        self._scroller.set_size(new_screen.get_size())

    def add_characters(self, *characters: Character) -> None:
        """Add characters to the map and add their sprites to the viewer."""
        self._map.add_characters(*characters)
        self.add_sprites(*(character.entity for character in characters))

    def show_layers(self, *layers: str) -> None:
        if not layers:
            layers = self._hidden_layers.keys()

        for layer in layers:
            sprites = self._hidden_layers[layer]
            self._hidden_layers[layer] = []
            index = self._map.get_layer_index(layer)
            self.add_sprites(*sprites, layer=index)

    def hide_layers(self, *layers: str) -> None:
        if not layers:
            layers = self._map.tmx.layernames

        for layer in layers:
            index = self._map.get_layer_index(layer)
            sprites = self._group.remove_sprites_of_layer(index)
            self._hidden_layers[layer] = sprites

    def replace_map(self, new_map: AdventureMap) -> None:
        """In theory, the method can be used to load a new map while keeping the same controller.
        In practice, switching maps is done within Game and all controllers are replaced
        on every single switch, so the method is only used during the construction.
        """
        assert new_map.loaded, "Cannot use not loaded map."

        self._map = new_map
        self._hidden_layers = {}
        self._scroller = BufferedRenderer(
            TiledMapData(new_map.tmx), size=self._screen.get_size())
        self._group = PyscrollGroup(
            self._scroller, default_layer=new_map.default_layer_index)
        self._collision_zones = ZoneList([
            Zone(Rect(obj.x, obj.y, obj.width, obj.height))
            for obj in new_map.collision_layer])
        self._trigger_zones = ZoneList([
            TriggerZone(Rect(obj.x, obj.y, obj.width, obj.height),
                        self.lua.execute(obj.properties["trigger"])) for obj in new_map.trigger_layer])
        self.add_sprites(*[char.entity for char in new_map.characters])

        self._hidden_layers = self._load_map_sprites(new_map)
        self.show_layers()

    def update(self, dt: float) -> None:
        self._group.update(dt)  # Update entities.
        self._map.update(dt)    # Update characters.

    def _load_map_sprites(self, new_map: AdventureMap) -> dict[str, list[Entity]]:
        return {layer.name: self._load_layer_sprites(layer) for layer in new_map.tmx.layers}

    def _load_layer_sprites(self, layer: TiledElement) -> list[Entity]:

        def supports_entity(obj: Any) -> bool:
            return isinstance(obj, TiledObject) and obj.image is not None

        def to_entity(obj: TiledObject) -> Entity:
            return Entity(image=obj.image,
                          position={"x": obj.x, "y": obj.y})

        return [to_entity(obj) for obj in layer if supports_entity(obj)]


class CollisionController:

    def __init__(self,
                 viewer: MapViewer,
                 ) -> None:

        self._viewer = viewer

    def update(self, dt: float) -> None:
        for character in self._viewer.characters:
            self._handle_collision(character, dt)

    def _handle_collision(self, character: Character, dt: float) -> None:
        if self._viewer.collision_zones.collides_sprite(character.entity):
            character.movement_controller.process_collision(dt)


class TriggerController:

    def __init__(self,
                 viewer: MapViewer,
                 tracked_characters: list[Character] | None = None,
                 ) -> None:

        self._tracked_characters = tracked_characters if tracked_characters else []
        self._viewer = viewer

    def start_tracking(self, character: Character) -> None:
        self._tracked_characters.append(character)

    def stop_tracking(self, character: Character) -> None:
        self._tracked_characters.remove(character)

    def update(self, dt: float) -> None:
        for character in self._tracked_characters:
            self._handle_triggers(character, dt)

    def invoke_use(self) -> None:
        for character in self._tracked_characters:
            self._handle_use(character)

    def _handle_triggers(self, character: Character, dt: float) -> None:
        old = character.entity.active_zones
        new = set(self._viewer.trigger_zones.get_all_colliding_zones(
            character.entity))

        just_left = old.difference(new)
        old.difference_update(just_left)
        for zone in just_left:
            zone.trigger.onExit(zone.trigger, character, self._viewer)

        just_entered = new.difference(old)
        old.update(just_entered)
        for zone in just_entered:
            zone.trigger.onEnter(zone.trigger, character, self._viewer)

    def _handle_use(self, character: Character) -> None:
        for zone in character.entity.active_zones:
            zone.trigger.onUse(zone.trigger, character, self._viewer)
