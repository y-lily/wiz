import pathlib
from typing import ClassVar

import pygame as pg
import pytest
from mock_app import MockApp, MockTrigger, create_screen
from pygame import freetype
from pygame.freetype import Font, SysFont
from pygame.surface import Surface

from src.sprites.sprite_keeper import SpriteKeeper
from src.ui import UI, Panel, PanelBuilder, Textbox
from src.ui.blueprint import WidgetTrigger
from src.ui.shared import Direction
from src.ui.textbox import TextSprite

TEXT_SAMPLE = ('"I can feel there is someone hiding behind the curtains."\n '
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


class TestTextSprite:

    _SCREEN_SIZE: ClassVar = (1280, 720)
    _PANEL_SIZE: ClassVar = (320, 240)

    @pytest.fixture
    def screen(self) -> Surface:
        return create_screen(self._SCREEN_SIZE)

    @pytest.fixture
    def ui(self, screen: Surface) -> UI:
        ui = UI(screen)
        ui.update(0.1)
        return ui
    
    @pytest.fixture
    def panel_builder(self) -> PanelBuilder:
        sprite_keeper = SpriteKeeper(pathlib.Path(__file__).parent)
        return PanelBuilder(sprite_keeper, "panel_32.png")
    
    @pytest.fixture
    def transparent_panel(self, panel_builder: PanelBuilder) -> Panel:
        return panel_builder.build_panel(self._PANEL_SIZE, alpha=True)
    
    @pytest.fixture
    def trigger(self) -> WidgetTrigger:
        return MockTrigger()
    
    @pytest.fixture
    def font(self) -> Font:
        freetype.init()
        return SysFont("Arial", 14)
    
    @pytest.fixture
    def textbox(self, transparent_panel: Panel, trigger: WidgetTrigger, font: Font) -> Textbox:
        return Textbox(TEXT_SAMPLE,
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
    
    @pytest.fixture
    def text_sprite(self, preadded_textbox: Textbox) -> TextSprite:
        return preadded_textbox._text_sprite
    
    def test_text_sprite_can_be_scrolled_downwards(self, ui: UI, text_sprite: TextSprite) -> None:
        text_sprite.scroll(Direction.DOWN)
        ui.update(0.1)
        assert text_sprite._scroller._position == (0, 1)

    def test_text_sprite_cannot_be_scrolled_downwards_from_the_last_line(self, ui: UI, text_sprite: TextSprite) -> None:
        scroll_to_limit(text_sprite, Direction.DOWN)
        ui.update(0.1)
        
        position_before = text_sprite._scroller._position
        
        text_sprite.scroll(Direction.DOWN)
        ui.update(0.1)

        position_after = text_sprite._scroller._position
        assert position_before == position_after

    def test_text_sprite_can_be_scrolled_upwards(self, ui: UI, text_sprite: TextSprite) -> None:
        text_sprite.scroll(Direction.DOWN)
        text_sprite.scroll(Direction.DOWN)
        ui.update(0.1)

        text_sprite.scroll(Direction.UP)
        ui.update(0.1)
        assert text_sprite._scroller._position == (0, 1)

    def test_text_sprite_cannot_be_scrolled_upwards_from_the_first_line(self, ui: UI, text_sprite: TextSprite) -> None:
        text_sprite.scroll(Direction.UP)
        ui.update(0.1)
        assert text_sprite._scroller._position == (0, 0)

    @pytest.mark.parametrize('direction', (Direction.LEFT, Direction.RIGHT))
    def test_text_sprite_cannot_be_scrolled_sideways(self, ui: UI, text_sprite: TextSprite, direction: Direction) -> None:
        text_sprite.scroll(direction)
        ui.update(0.1)
        assert text_sprite._scroller._position == (0, 0)

    def test_first_word_is_visible_when_on_the_first_line(self, text_sprite: TextSprite) -> None:
        scroller = text_sprite._scroller
        first_word = scroller._data[0]
        assert scroller.is_visible(first_word)

    def test_first_word_is_not_visible_when_scrolled_out(self, ui: UI, text_sprite: TextSprite) -> None:
        text_sprite.scroll(Direction.DOWN)
        ui.update(0.1)

        scroller = text_sprite._scroller
        first_word = scroller._data[0]
        assert not scroller.is_visible(first_word)

    def test_last_word_is_visible_when_on_the_last_line(self, ui: UI, text_sprite: TextSprite) -> None:
        scroll_to_limit(text_sprite, Direction.DOWN)
        ui.update(0.1)

        scroller = text_sprite._scroller
        last_word = scroller._data[-1]
        assert scroller.is_visible(last_word)

    def test_last_word_is_not_visible_when_scrolled_out(self, ui: UI, text_sprite: TextSprite) -> None:
        scroll_to_limit(text_sprite, Direction.DOWN)
        text_sprite.scroll(Direction.UP)
        ui.update(0.1)

        scroller = text_sprite._scroller
        last_word = scroller._data[-1]
        assert not scroller.is_visible(last_word)

    def test_scaling_up_makes_more_words_visible(self, ui: UI, text_sprite: TextSprite) -> None:
        scroller = text_sprite._scroller
        visible_before = scroller.get_visible()

        text_sprite.scale((1.4, 1.4))
        ui.update(0.1)

        visible_after = scroller.get_visible()
        assert len(visible_after) > len(visible_before)

    def test_scaling_down_makes_less_words_visible(self, ui: UI, text_sprite: TextSprite) -> None:
        scroller = text_sprite._scroller
        visible_before = scroller.get_visible()

        text_sprite.scale((0.4, 0.4))
        ui.update(0.1)

        visible_after = scroller.get_visible()
        assert len(visible_after) < len(visible_before)

    def test_unused_space_fits_after_scaling(self, ui: UI, text_sprite: TextSprite) -> None:
        scroll_to_limit(text_sprite, Direction.DOWN)
        ui.update(0.1)
        scroller = text_sprite._scroller
        position_before = scroller._position
        
        text_sprite.scale((1.4, 1.4))
        ui.update(0.1)

        position_after = scroller._position
        assert position_before != position_after
        

def scroll_to_limit(sprite: TextSprite, direction: Direction) -> None:
    while sprite.can_scroll(direction):
        sprite.scroll(direction)


if __name__ == "__main__":
    pg.init()
    screen = create_screen((1280, 720))
    ui = UI(screen)
    keeper = SpriteKeeper(pathlib.Path(__file__).parent)
    panel_builder = PanelBuilder(keeper, "panel_32.png")
    panel = panel_builder.build_panel((320, 240), alpha=True)
    textbox = Textbox(TEXT_SAMPLE, panel, MockTrigger(), (32, 32, 32, 32), SysFont("Arial", 14))
    ui.add(textbox)
    
    app = MockApp(screen, ui)
    app.run()
