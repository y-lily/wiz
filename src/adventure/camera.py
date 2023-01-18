from typing import TYPE_CHECKING, Optional

import pyscroll
import pytmx
from pygame.rect import Rect
from pygame.sprite import Sprite
from pygame.surface import Surface
from typing_extensions import override

from src.adventure.entity import Entity
from src.adventure.shared import Path


class Camera:

    def __init__(self,
                 screen: Surface,
                 tmx_path: Path,
                 ) -> None:

        self._screen = screen
        tmx = pytmx.load_pygame(tmx_path)

        self._map_layer = pyscroll.BufferedRenderer(
            pyscroll.data.TiledMapData(tmx),
            size=screen.get_size())
        self._group = pyscroll.PyscrollGroup(self._map_layer)

    @property
    def layers(self) -> list[pytmx.TiledElement]:
        return list(self._map_layer.data.tmx.layers)

    @property
    def zoom(self) -> float:
        if TYPE_CHECKING:
            assert isinstance(self._map_layer.zoom, float)
        return self._map_layer.zoom

    @zoom.setter
    def zoom(self, new_value: float) -> None:
        self._map_layer.zoom = new_value

    def add_sprites(self,
                    *sprites: Sprite,
                    layer: Optional[int] = None,
                    ) -> None:

        self._group.add(sprites, layer=layer)

    def remove_sprites(self, *sprites: Sprite) -> None:
        self._group.remove(sprites)

    def center(self, pixel: tuple[int, int]) -> None:
        self._group.center(pixel)

    def draw(self) -> None:
        self._group.draw(self._screen)

    def set_screen(self, new_screen: Surface) -> None:
        self._screen = new_screen
        self._map_layer.set_size(new_screen.get_size())

    def update(self, dt: float) -> None:
        self._group.update(dt)

    def get_layer(self, name: str) -> pytmx.TiledElement:
        return self._map_layer.data.tmx.get_layer_by_name(name)

    def get_layer_index(self, name: str) -> int:
        return next(index for index, layer in enumerate(self.layers) if layer.name == name)


class AdventureCamera(Camera):

    def __init__(self,
                 screen: Surface,
                 tmx_path: Path,
                 ) -> None:

        super().__init__(screen, tmx_path)

        self._default_layer = self.get_layer_index("sprites")
        self._collision_zones = self._load_layer_rects("collisions")
        self._interaction_zones = self._load_layer_rects("interaction_zones")
        self._interactive_objects = self._load_plain_objects(
            "interaction_zones")

        self._roof_sprites = self._load_layer_sprites("roof")
        self.show_roof()

    @property
    def collision_zones(self) -> tuple[Rect, ...]:
        return tuple(self._collision_zones)

    @property
    def interaction_zones(self) -> tuple[Rect, ...]:
        return tuple(self._interaction_zones)

    @override
    def add_sprites(self,
                    *sprites: Sprite,
                    layer: Optional[int] = None,
                    ) -> None:

        layer = layer if layer is not None else self._default_layer
        super().add_sprites(*sprites, layer=layer)

    def get_interactive_object(self, index: int) -> pytmx.TiledObject:
        return self._interactive_objects[index]

    def show_roof(self) -> None:
        roof_index = self.get_layer_index("roof")
        self.add_sprites(*self._roof_sprites, layer=roof_index)

    def hide_roof(self) -> None:
        self.remove_sprites(*self._roof_sprites)

    def _load_layer_rects(self, layer_name: str) -> list[Rect]:
        layer = self.get_layer(layer_name)
        return [Rect(obj.x,
                     obj.y,
                     obj.width,
                     obj.height) for obj in layer]

    def _load_layer_sprites(self, layer_name: str) -> list[Sprite]:
        layer = self.get_layer(layer_name)
        return [Entity(obj.image,
                       (obj.x, obj.y)) for obj in layer]

    def _load_plain_objects(self, layer_name: str) -> list[pytmx.TiledObject]:
        layer = self.get_layer(layer_name)
        return [obj for obj in layer]
