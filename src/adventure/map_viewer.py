from contextlib import suppress
from typing import Any, Optional, Sequence

from pygame.event import Event
from pygame.sprite import Sprite
from pygame.surface import Surface
from pyscroll import BufferedRenderer, PyscrollGroup
from pyscroll.data import TiledMapData
from pytmx import TiledElement, TiledObject

from .adventure_map import AdventureMap, TriggerZone, Zone, ZoneList
from .character import Character
from .entity import Entity


class MapViewer:

    _scroller: BufferedRenderer
    _group: PyscrollGroup
    _trigger_zones: ZoneList[TriggerZone]
    _collision_zones: ZoneList[Zone]
    _map: AdventureMap
    _hidden_layers: dict[str, list[Entity]]

    def __init__(self,
                 new_map: AdventureMap | None = None,
                 screen: Surface | None = None,
                 ) -> None:

        if screen is not None:
            self._screen = screen
        if new_map is not None:
            self.set_map(new_map)  # Load scroller, group, zones, sprites.

    @property
    def collision_zones(self) -> ZoneList[Zone]:
        # return self._collision_zones
        return self._map.collision_zones

    @property
    def trigger_zones(self) -> ZoneList[TriggerZone]:
        # return self._trigger_zones
        return self._map.trigger_zones

    @property
    def zoom(self) -> float:
        return float(self._scroller.zoom)

    @zoom.setter
    def zoom(self, new_value: float) -> None:
        self._scroller.zoom = new_value

    # @property
    # def sprites(self) -> list[Sprite]:
    #     return self._group.sprites()

    def add_sprites(self, *sprites: Sprite, layer: Optional[int] = None) -> None:
        self._group.add(*sprites, layer=layer)

    def remove_sprites(self, *sprites: Sprite) -> None:
        self._group.remove(*sprites)

    def center(self, pixel: tuple[int, int]) -> None:
        self._group.center(pixel)

    def draw(self) -> None:
        self._group.draw(self._screen)

    def set_screen(self, screen: Surface) -> None:
        self._screen = screen
        with suppress(AttributeError):
            self._scroller.set_size(screen.get_size())

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

    def set_map(self, new_map: AdventureMap) -> None:
        """Set a new map to be viewed. The viewer's sprite group will be replaced with this map's sprites.
        The map has to be already loaded in order for the character sprites to be added into the group."""
        # assert new_map.loaded, "Cannot use not loaded map."
        if not new_map.loaded:
            print(
                "WARNING: The map is not loaded; character sprites should be added manually.")

        self._map = new_map
        self._hidden_layers = {}
        self._scroller = BufferedRenderer(TiledMapData(new_map.tmx),
                                          size=self._screen.get_size())

        self._group = PyscrollGroup(
            self._scroller, default_layer=new_map.default_layer)
        for char in new_map.characters:
            self.add_sprites(char.entity)

        self._hidden_layers = self._load_map_sprites(new_map)
        self.show_layers()

    def update_sprites(self, dt: float) -> None:
        self._group.update(dt)

    def update_characters(self, dt: float) -> None:
        self._map.update(dt)

    def get_center_offset(self) -> tuple[int, int]:
        return tuple(self._scroller.get_center_offset())

    def _load_map_sprites(self, new_map: AdventureMap) -> dict[str, list[Entity]]:
        return {layer.name: self._load_layer_sprites(layer) for layer in new_map.tmx.layers}

    def _load_layer_sprites(self, layer: TiledElement) -> list[Entity]:

        def supports_entity(obj: Any) -> bool:
            return isinstance(obj, TiledObject) and obj.image is not None

        def to_entity(obj: TiledObject) -> Entity:
            return Entity(image=obj.image,
                          position={"x": obj.x, "y": obj.y})

        return [to_entity(obj) for obj in layer if supports_entity(obj)]
