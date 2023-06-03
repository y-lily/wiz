import pathlib
from typing import ClassVar

import pygame as pg
import pytest
from mock_app import MockApp, create_screen
from pygame import Surface, freetype
from pygame.freetype import Font, SysFont
from pytest_lazyfixture import lazy_fixture

from src.sprites.sprite_keeper import SpriteKeeper
from src.ui import UI, Panel, PanelBuilder, Textbox
from src.ui.decorators import AnimatedTextbox, AutoscrollingTextbox, FadingWidget
from src.ui.shared import Direction
from src.ui.textbox import TextSprite
from src.ui.widget import WidgetTrigger

TEXT_SAMPLE_1 = ('"I can feel there is someone hiding behind the curtains."\n '
                 '"Don\'t bother me with such nonsense."\n '
                 '"It is not nonsense. There is definitely a person and who knows what do they have in mind?"\n '
                 '"You have important things to do."\n '
                 '"How are they more important than the potential source of danger right under our noses? We can\'t just leave it be, we have to find out what are their intentions."\n '
                 '"You shall get back to business."\n '
                 '"Can we at the very least take a look at them?"\n '
                 '"This is not relevant to your duties."\n '
                 '"Hey, I\'m not even sure it\'s a human being anymore!"\n '
                 '"Stop wasting my time."'
                 )

TEXT_SAMPLE_2 = "Sometimes things can happen just like this."


class TestTextbox:

    _SCREEN_SIZE: ClassVar = (1280, 720)
    _PANEL_SIZE: ClassVar = (320, 240)
    _BIG_PANEL_SIZE: ClassVar = (640, 402)

    @pytest.fixture
    def screen(self) -> Surface:
        return create_screen(self._SCREEN_SIZE)

    @pytest.fixture
    def ui(self, screen: Surface) -> UI:
        ui = UI(screen)
        ui.update(0.1)
        return ui

    @pytest.fixture
    def sprite_keeper(self) -> SpriteKeeper:
        return SpriteKeeper(pathlib.Path(__file__).parent)

    @pytest.fixture
    def panel_builder(self, sprite_keeper: SpriteKeeper) -> PanelBuilder:
        return PanelBuilder(sprite_keeper, "panel_32.png")

    @pytest.fixture
    def transparent_panel(self, panel_builder: PanelBuilder) -> Panel:
        return panel_builder.build_panel(self._PANEL_SIZE, alpha=True)

    @pytest.fixture
    def big_panel(self, panel_builder: PanelBuilder) -> Panel:
        return panel_builder.build_panel(self._BIG_PANEL_SIZE, alpha=True)

    @pytest.fixture
    def trigger(self) -> WidgetTrigger:
        return WidgetTrigger()

    @pytest.fixture
    def font(self) -> Font:
        freetype.init()
        return SysFont("Arial", 14)

    @pytest.fixture
    def textbox(self, transparent_panel: Panel, trigger: WidgetTrigger, font: Font) -> Textbox:
        return Textbox(TEXT_SAMPLE_1,
                       transparent_panel,
                       trigger,
                       (32, 32, 32, 32),
                       font,
                       )

    @pytest.fixture
    def preadded_textbox(self, ui: UI, textbox: Textbox) -> Textbox:
        ui.add(textbox)
        ui.update(0.1)
        return textbox

    def test_ui_contains_animated_textbox(self, ui: UI, textbox: Textbox) -> None:
        widget = AnimatedTextbox(textbox, 20)
        ui.add(widget)
        ui.update(0.1)

        assert widget in ui._widgets

    def test_kill_removes_animated_textbox_from_ui(self, ui: UI, textbox: Textbox) -> None:
        widget = AnimatedTextbox(textbox, 20)
        ui.add(widget)
        ui.update(0.1)
        widget.kill()
        ui.update(0.1)

        assert widget not in ui._widgets

    def test_animated_textbox_raises_text_length_with_time(self, ui: UI, textbox: Textbox) -> None:
        textbox = AnimatedTextbox(textbox, 20)
        ui.add(textbox)
        ui.update(0.1)

        text_before = textbox._text_sprite._text

        for _ in range(100):
            ui.update(0.1)

        text_after = textbox._text_sprite._text

        assert len(text_after) > len(text_before)


if __name__ == "__main__":
    pg.init()
    screen = create_screen((1280, 720))
    ui = UI(screen)
    keeper = SpriteKeeper(pathlib.Path(__file__).parent)
    panel_builder = PanelBuilder(keeper, "panel_32.png")

    panel = panel_builder.build_panel((320, 240), alpha=True)
    textbox = Textbox(TEXT_SAMPLE_1, panel, WidgetTrigger(),
                      (32, 32, 32, 32), SysFont("Arial", 14), editable=True)

    # fading_textbox = FadingWidget(textbox, 3)
    animated_textbox = AnimatedTextbox(textbox, 30)
    # autoscrolling_textbox = AutoscrollingTextbox(animated_textbox)

    # ui.add(textbox, centered=True)
    # ui.add(fading_textbox)
    ui.add(animated_textbox)
    # ui.add(autoscrolling_textbox)

    app = MockApp(screen, ui)
    app.run()
