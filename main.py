import cProfile
import pathlib
import pstats

import pygame as pg

from src.adventure import MapLoader
from src.game import Game
from src.sprites import SpriteKeeper

RESOURCE_DIR = pathlib.Path(__file__).parent / "res"
SCREEN_SIZE = (720, 480)
HERO_DEF = RESOURCE_DIR / "hero_def.lua"
MAP_DEF = RESOURCE_DIR / "room_1_def.lua"


def main() -> None:
    pg.init()
    map_loader = MapLoader(resource_dir=RESOURCE_DIR)
    sprite_keeper = SpriteKeeper(resource_dir=RESOURCE_DIR)
    game = Game(screen_size=SCREEN_SIZE,
                map_loader=map_loader,
                sprite_keeper=sprite_keeper,
                )
    game.load_hero(HERO_DEF)
    game.load_map(MAP_DEF, entry_point="default")
    game.run()


if __name__ == "__main__":
    with cProfile.Profile() as p:
        main()

    info = pstats.Stats(p)
    info.sort_stats(pstats.SortKey.TIME)
    info.print_stats(30)
