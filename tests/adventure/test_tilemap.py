from enum import Enum

import pygame
import pytmx
import pytmx.util_pygame

from lib.assert_never import assert_never

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720


class Direction(Enum):

    UP = 1
    RIGHT = 2
    DOWN = 3
    LEFT = 4
    ASCEND = 5
    DESCEND = 6


class Adventurer:

    def __init__(self, _image_filename: str, _x: int = 0, _y: int = 0, _layer: int = 0) -> None:
        self._image = pygame.image.load(_image_filename).convert()
        self._x = _x
        self._y = _y
        self._layer = _layer

    @property
    def image(self) -> pygame.surface.Surface:
        return self._image

    @property
    def x(self) -> int:
        return self._x

    @property
    def y(self) -> int:
        return self._y

    @property
    def layer(self) -> int:
        return self._layer

    def move(self, direction: Direction, tilemap: pytmx.TiledMap) -> bool:
        if direction is Direction.UP:
            return self.jump(tilemap, self._x, self._y-1, self._layer)
        if direction is Direction.RIGHT:
            return self.jump(tilemap, self._x+1, self._y, self._layer)
        if direction is Direction.DOWN:
            return self.jump(tilemap, self._x, self._y+1, self._layer)
        if direction is Direction.LEFT:
            return self.jump(tilemap, self._x-1, self._y, self._layer)
        if direction is Direction.ASCEND:
            return self.jump(tilemap, self._x, self._y, self._layer+1)
        if direction is Direction.DESCEND:
            return self.jump(tilemap, self._x, self._y, self._layer-1)

        assert_never(direction)

    def jump(self, tilemap: pytmx.TiledMap, x: int, y: int, layer: int | None = None) -> bool:
        layer = layer if layer is not None else self._layer

        try:
            tile_properties = tilemap.get_tile_properties(x, y, layer)
        except ValueError:
            return False
        except Exception as e:
            # For whatever reason pytmx raises exceptions of pure Exception class.
            if type(e) == Exception:
                return False
            else:
                raise Exception from e

        if tile_properties is None or not tile_properties.get("impassable", False):
            self._x = x
            self._y = y
            self._layer = layer
            return True

        return False


def _tile_floor(tilemap: pytmx.TiledMap, x: int, y: int) -> tuple[int, int]:
    return (x+0.5)*tilemap.tilewidth, (y+1)*tilemap.tileheight


if __name__ == "__main__":
    # Set up the window.
    pygame.init()
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    # Set up the map and the adventurer.
    tilemap = pytmx.util_pygame.load_pygame("test_tilemap.tmx")
    tilewidth = tilemap.tilewidth
    tileheight = tilemap.tileheight
    layer: pytmx.TiledObject = tilemap.layers[0]
    adventurer = Adventurer("test_hero.png", 1, 1, 0)
    game_loop = True

    while game_loop:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # TODO: Save game state.
                exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    adventurer.move(Direction.UP, tilemap)
                elif event.key == pygame.K_RIGHT:
                    adventurer.move(Direction.RIGHT, tilemap)
                elif event.key == pygame.K_DOWN:
                    adventurer.move(Direction.DOWN, tilemap)
                elif event.key == pygame.K_LEFT:
                    adventurer.move(Direction.LEFT, tilemap)
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()

        window.fill((255, 255, 255))
        # TODO: Only render visible tiles.
        for layer in reversed(tilemap.layers):
            for x, y, image in layer.tiles():
                window.blit(
                    image, (x*tilewidth, y*tileheight, tilewidth, tileheight))

        x, y = _tile_floor(tilemap, adventurer.x, adventurer.y)
        window.blit(adventurer.image, (x-adventurer.image.get_width() /
                    2, y-adventurer.image.get_height()))

        pygame.display.flip()
        clock.tick(60)
