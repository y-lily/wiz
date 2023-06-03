import pathlib

import pygame as pg
from mock_app import MockApp, create_screen
from test_textbox import TEXT_SAMPLE_1, TEXT_SAMPLE_2

from src.sprites.sprite_keeper import SpriteKeeper
from src.ui import UI, Dialogue, PanelBuilder
from src.ui.widget import WidgetTrigger

if __name__ == "__main__":
    pg.init()
    screen = create_screen((1280, 720))
    ui = UI(screen)
    keeper = SpriteKeeper(pathlib.Path(__file__).parent)
    panel_builder = PanelBuilder(keeper, "panel_32.png")

    big_panel = panel_builder.build_panel((640, 402), alpha=True)
    portrait_1 = keeper.sprite("portrait_1.png", alpha=False).extract_whole()
    portrait_2 = keeper.sprite("portrait_2.png", alpha=False).extract_whole()

    def on_use(trigger: WidgetTrigger, widget: Dialogue) -> None:
        if not hasattr(trigger, "_portrait_id"):
            trigger._portrait_id = 1

        if trigger._portrait_id == 1:
            widget.set_params(new_header="Finn",
                              new_portrait=portrait_2, new_text=TEXT_SAMPLE_2)
            trigger._portrait_id = 2
        elif trigger._portrait_id == 2:
            widget.set_params(new_header="Sheril",
                              new_portrait=portrait_1, new_text=TEXT_SAMPLE_1)
            trigger._portrait_id = 1

    dialogue = Dialogue("", portrait_1, "Sheril", big_panel,
                        WidgetTrigger(on_use=on_use), (32, 32, 32, 32))
    ui.add(dialogue)

    app = MockApp(screen, ui)
    app.run()
