from contextlib import suppress
from typing import Any

from pygame import Rect, Surface
from pygame.sprite import Sprite
from pyscroll import BufferedRenderer, PyscrollGroup
from pyscroll.data import TiledMapData
from pytmx import TiledElement, TiledObject
from transitions import core

# TODO:
# from shared import pair
from src.shared import pair

from .adventure_map import AdventureMap, TriggerZone, Zone, ZoneList
from .character import Character
from .entity import Entity


class MapViewer:

    _group: PyscrollGroup
    _hidden_layers: dict[str, list[Entity]]
    _map: AdventureMap
    _renderer: BufferedRenderer

    def __init__(self,
                 adventure_map: AdventureMap | None = None,
                 screen: Surface | None = None,
                 ) -> None:

        if screen is not None:
            self._screen = screen

        if adventure_map is not None:
            self.set_map(adventure_map)

    @property
    def collision_zones(self) -> ZoneList[Zone]:
        return self._map.collision_zones

    @property
    def trigger_zones(self) -> ZoneList[TriggerZone]:
        return self._map.trigger_zones

    @property
    def zoom(self) -> float:
        return float(self._renderer.zoom)

    @zoom.setter
    def zoom(self, new_value: float) -> None:
        self._renderer.zoom = new_value

    def add_characters(self, *characters: Character) -> None:
        """Add characters to the map and add their sprites to the viewer."""

        self._map.add_characters(*characters)
        self.add_sprites(*(character.entity for character in characters))

    def add_sprites(self, *sprites: Sprite, layer: int | None = None) -> None:
        self._group.add(*sprites, layer=layer)

    def center(self, pixel: pair[int]) -> None:
        self._group.center(pixel)

    def draw(self) -> list[Rect]:
        return list(core.listify(self._group.draw(self._screen)))

    def get_center_offset(self) -> pair[int]:
        return self._renderer.get_center_offset()

    def hide_layers(self, *layers: str) -> None:
        if not layers:
            layers = self._map.tmx.layernames.keys()

        for layer in layers:
            layer_index = self._map.get_layer_index(layer)
            layer_sprites = self._group.remove_sprites_of_layer(layer_index)
            self._hidden_layers[layer] = layer_sprites

    def remove_sprites(self, *sprites: Sprite) -> None:
        self._group.remove(*sprites)

    def set_map(self, new_map: AdventureMap) -> None:
        """Set a new map to be viewed. The viewer's sprite group will be replaced with this map's sprites.
        The map has to be already loaded in order for the character sprites to be added into the group."""

        if not new_map.loaded:
            print(
                "WARNING: The map is not loaded; character sprites should be added manually.")

        self._map = new_map
        self._hidden_layers = {}
        self._renderer = BufferedRenderer(TiledMapData(new_map.tmx),
                                          size=self._screen.get_size())
        self._group = PyscrollGroup(self._renderer,
                                    default_layer=new_map.default_layer)

        for character in new_map.characters:
            self.add_sprites(character.entity)

        self._hidden_layers = self._load_map_sprites(new_map)
        self.show_layers()

    def set_screen(self, screen: Surface) -> None:
        self._screen = screen
        with suppress(AttributeError):
            self._renderer.set_size(screen.get_size())

    def show_layers(self, *layers: str) -> None:
        if not layers:
            layers = tuple(self._hidden_layers.keys())

        for layer in layers:
            sprites = self._hidden_layers[layer]
            self._hidden_layers[layer] = []
            index = self._map.get_layer_index(layer)
            self.add_sprites(*sprites, layer=index)

    def update_characters(self, dt: float) -> None:
        self._map.update(dt)

    def update_sprites(self, dt: float) -> None:
        self._group.update(dt)

    def _load_map_sprites(self, new_map: AdventureMap) -> dict[str, list[Entity]]:
        return {layer.name: self._load_layer_sprites(layer) for layer in new_map.tmx.layers}

    def _load_layer_sprites(self, layer: TiledElement) -> list[Entity]:

        def supports_entity(obj: Any) -> bool:
            return isinstance(obj, TiledObject) and obj.image is not None

        def to_entity(obj: TiledObject) -> Entity:
            return Entity(image=obj.image,
                          position={"x": obj.x, "y": obj.y})

        return [to_entity(obj) for obj in layer if supports_entity(obj)]
