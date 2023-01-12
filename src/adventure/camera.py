import pathlib

import pygame
import pyscroll
import pytmx
from sprite import Sprite
from typing_extensions import override


class Camera:

    def __init__(self,
                 _screen: pygame.surface.Surface,
                 _tmx_path: str | pathlib.Path) -> None:
        self._screen = _screen

        tmx = pytmx.load_pygame(_tmx_path)
        self._map_layer = pyscroll.BufferedRenderer(
            pyscroll.data.TiledMapData(tmx),
            size=_screen.get_size())

        self._group = pyscroll.PyscrollGroup(
            self._map_layer)

    @property
    def layers(self) -> list[pytmx.TiledElement]:
        return list(self._map_layer.data.tmx.layers)

    @property
    def zoom(self) -> float:
        assert isinstance(self._map_layer.zoom, float)
        return self._map_layer.zoom

    @zoom.setter
    def zoom(self, new_value: float) -> None:
        self._map_layer.zoom = new_value

    @property
    def sprites(self) -> list[pygame.sprite.Sprite]:
        sprites: list[pygame.sprite.Sprite] = self._group.sprites()
        return sprites

    def add_sprites(self, *sprites: Sprite, layer: int | None = None) -> None:
        self._group.add(sprites, layer=layer)

    def remove_sprites(self, *sprites: Sprite) -> None:
        self._group.remove(sprites)

    def center(self, pixel: tuple[int, int]) -> None:
        self._group.center(pixel)

    def draw(self) -> None:
        self._group.draw(self._screen)

    def get_layer_index(self, name: str) -> int:
        return next(n for n, layer in enumerate(self.layers) if layer.name == name)

    def get_layer(self, name: str) -> pytmx.TiledElement:
        return self._map_layer.data.tmx.get_layer_by_name(name)

    def set_screen(self, screen: pygame.surface.Surface) -> None:
        self._screen = screen
        self._map_layer.set_size(screen.get_size())

    def update(self, dt: float) -> None:
        self._group.update(dt)


class AdventureCamera(Camera):

    def __init__(self, _screen: pygame.surface.Surface, _tmx_path: str | pathlib.Path) -> None:
        super().__init__(_screen, _tmx_path)

        self._default_layer = self.get_layer_index("sprites")
        self._collisions = self._load_collisions()

        self._roof_sprites = self._load_roof_sprites()
        self.show_roof()

    @property
    def collisions(self) -> list[pygame.Rect]:
        return self._collisions

    @override
    def add_sprites(self, *sprites: Sprite, layer: int | None = None) -> None:
        if layer is None:
            layer = self._default_layer
        super().add_sprites(*sprites, layer=layer)

    def show_roof(self) -> None:
        roof_index = self.get_layer_index("roof")
        self.add_sprites(*self._roof_sprites, layer=roof_index)

    def hide_roof(self) -> None:
        self.remove_sprites(*self._roof_sprites)

    def _load_roof_sprites(self) -> list[Sprite]:
        roof_layer = self.get_layer("roof")
        sprites = [Sprite(image=obj.image, position=(obj.x, obj.y))
                   for obj in roof_layer]
        return sprites

    def _load_collisions(self) -> list[pygame.Rect]:
        collision_layer = self.get_layer("collisions")
        collisions = [pygame.Rect(
            obj.x, obj.y, obj.width, obj.height) for obj in collision_layer]
        return collisions
