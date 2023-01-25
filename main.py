import pathlib

import pygame

from src.adventure import Game


def main() -> None:
    res_dir = pathlib.Path(__file__).parent / "res"
    map_def_path = res_dir / "room_1_def.lua"
    hero_def_path = res_dir / "hero_def.lua"
    pygame.init()
    screen = pygame.display.set_mode((1280, 720), pygame.RESIZABLE)
    game = Game(screen, map_def_path, hero_def_path)
    game.run()


if __name__ == "__main__":
    main()
