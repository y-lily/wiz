import pathlib

import pygame as pg
from mock_app import MockApp, create_screen

from src.sprites import SpriteKeeper
from src.ui import UI, ProgressBar
from src.ui.panel import PanelBuilder
from src.ui.widget import WidgetTrigger

if __name__ == "__main__":
    pg.init()
    screen = create_screen((1280, 720))
    ui = UI(screen)
    keeper = SpriteKeeper(pathlib.Path(__file__).parent)
    panel_builder = PanelBuilder(keeper, "panel_32.png")

    panel = panel_builder.build_panel((300, 128), alpha=True)
    empty_bar = panel_builder.build_panel(
        (200, 64), path="grey_bar_32.png", alpha=True)
    filled_bar = panel_builder.build_panel(
        (200, 64), path="red_bar_32.png", alpha=True)

    widget = ProgressBar(panel, WidgetTrigger(),
                         empty_bar, filled_bar, (50, 32), 80)

    ui.add(widget)
    app = MockApp(screen, ui)
    app.run()
