import pathlib
from typing import Any, ClassVar

import pygame as pg
import pytest
from mock_app import MockApp, MockTrigger, create_screen
from pygame.surface import Surface
from pytest_lazyfixture import lazy_fixture

from src.sprites.sprite_keeper import SpriteKeeper
from src.ui import UI, Panel, PanelBuilder, Widget, tuple_math


class TestWidget:

    _SCREEN_SIZE: ClassVar = (1280, 720)
    _SMALL_PANEL_SIZE: ClassVar = (320, 256)
    _PANEL_SIZE: ClassVar = (640, 480)

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
    def small_transparent_panel(self, panel_builder: PanelBuilder) -> Panel:
        return panel_builder.build_panel(self._SMALL_PANEL_SIZE, alpha=True)
    
    @pytest.fixture
    def transparent_panel(self, panel_builder: PanelBuilder) -> Panel:
        return panel_builder.build_panel(self._PANEL_SIZE, alpha=True)

    @pytest.fixture
    def trigger(self) -> MockTrigger:
        return MockTrigger()
    
    @pytest.fixture
    def small_widget(self, small_transparent_panel: Panel, trigger: MockTrigger) -> Widget:
        return Widget(small_transparent_panel, trigger)

    @pytest.fixture
    def widget(self, transparent_panel: Panel, trigger: MockTrigger) -> Widget:
        return Widget(transparent_panel, trigger)
    
    @pytest.fixture
    def preadded_widget(self, ui: UI, widget: Widget) -> Widget:
        ui.add(widget)
        ui.update(0.1)
        return widget
    
    @pytest.fixture
    def preadded_child(self, ui: UI, small_widget: Widget, preadded_widget: Widget) -> Widget:
        preadded_widget.add(small_widget)
        ui.update(0.1)
        return small_widget

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_scale_resizes_widget_and_its_children(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        size_before = target.get_size()

        preadded_widget.scale((1.1, 1.1))
        ui.update(0.1)

        size_after = target.get_size()
        assert size_before != size_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_scale_to_the_current_factor_does_not_resize_widget_and_its_children(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        size_before = target.get_size()

        preadded_widget.scale((1.0, 1.0))
        ui.update(0.1)

        size_after = target.get_size()
        assert size_before == size_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_shift_scale_resizes_widget_and_its_children(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        size_before = target.get_size()

        preadded_widget.shift_scale((0.1, 0.1))
        ui.update(0.1)
        
        size_after = target.get_size()
        assert size_before != size_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_shift_scale_of_zeros_does_not_resize_widget_and_its_children(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        size_before = target.get_size()

        preadded_widget.shift_scale((0.0, 0.0))
        ui.update(0.1)
        
        size_after = target.get_size()
        assert size_before == size_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_ui_scale_resizes_widget_and_its_children(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        size_before = target.get_size()

        ui.scale((1.1, 1.1))
        ui.update(0.1)

        size_after = target.get_size()
        assert size_before != size_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_ui_scale_to_the_current_factor_does_not_resize_widget_and_its_children(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        size_before = target.get_size()

        ui.scale((1.0, 1.0))
        ui.update(0.1)

        size_after = target.get_size()
        assert size_before == size_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_ui_shift_scale_resizes_widget_and_its_children(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        size_before = target.get_size()

        ui.shift_scale((0.1, 0.1))
        ui.update(0.1)

        size_after = target.get_size()
        assert size_before != size_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_ui_shift_scale_of_zeros_does_not_resize_widget_and_its_children(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        size_before = target.get_size()

        ui.shift_scale((0.0, 0.0))
        ui.update(0.1)

        size_after = target.get_size()
        assert size_before == size_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_set_offset_base_moves_widget_and_its_children_backgrounds(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        position_before = target._background.rect.topleft

        preadded_widget.set_offset_base((1, 1))
        ui.update(0.1)

        position_after = target._background.rect.topleft
        assert position_before != position_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_set_offset_base_to_the_current_value_does_not_move_widget_and_its_children_backgrounds(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        position_before = target._background.rect.topleft

        preadded_widget.set_offset_base((0, 0))
        ui.update(0.1)

        position_after = target._background.rect.topleft
        assert position_before == position_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_shift_offset_base_moves_widget_and_its_children_backgrounds(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        position_before = target._background.rect.topleft

        preadded_widget.shift_offset_base((1, 1))
        ui.update(0.1)

        position_after = target._background.rect.topleft
        assert position_before != position_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_shift_offset_base_with_zeros_does_not_move_widget_and_its_children_backgrounds(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        position_before = target._background.rect.topleft

        preadded_widget.shift_offset_base((0, 0))
        ui.update(0.1)

        position_after = target._background.rect.topleft
        assert position_before == position_after

    @pytest.mark.parametrize('centered', (True, False))
    def test_setting_centered_moves_widget_background(self, ui: UI, widget: Widget, centered: bool) -> None:
        ui.add(widget, centered)
        ui.update(0.1)

        position_before = widget._background.rect.topleft

        widget.centered = not centered
        ui.update(0.1)

        position_after = widget._background.rect.topleft
        assert position_before != position_after

    @pytest.mark.parametrize('centered', (True, False))
    def test_setting_centered_to_the_same_value_does_not_move_widget_background(self, ui: UI, widget: Widget, centered: bool) -> None:
        ui.add(widget, centered)
        ui.update(0.1)

        position_before = widget._background.rect.topleft

        widget.centered = centered
        ui.update(0.1)

        position_after = widget._background.rect.topleft
        assert position_before == position_after

    @pytest.mark.parametrize('centered', (True, False))
    def test_setting_parent_centered_moves_child_background(self, ui: UI, widget: Widget, small_widget: Widget, centered: bool) -> None:
        ui.add(widget, centered)
        widget.add(small_widget)
        ui.update(0.1)

        position_before = small_widget._background.rect.topleft
        
        widget.centered = not centered
        ui.update(0.1)

        position_after = small_widget._background.rect.topleft
        assert position_before != position_after
    
    @pytest.mark.parametrize('centered', (True, False))
    def test_setting_parent_centered_to_the_same_value_does_not_move_child_background(self, ui: UI, widget: Widget, small_widget: Widget, centered: bool) -> None:
        ui.add(widget, centered)
        widget.add(small_widget)
        ui.update(0.1)

        position_before = small_widget._background.rect.topleft
        
        widget.centered = centered
        ui.update(0.1)

        position_after = small_widget._background.rect.topleft
        assert position_before == position_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_center_at_moves_widget_and_its_children_backgrounds(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        center_before = target._background.rect.center

        position = tuple_math.add(preadded_widget._background.rect.center,
                                  (1, 1))
        preadded_widget.center_at(position)
        ui.update(0.1)

        center_after = target._background.rect.center
        assert center_before != center_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_center_at_the_same_position_does_not_move_widget_and_its_children_backgrounds(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        ui.update(0.1)

        center_before = target._background.rect.center

        preadded_widget.center_at(preadded_widget._background.rect.center)
        ui.update(0.1)

        center_after = target._background.rect.center
        assert center_before == center_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_position_at_moves_widget_and_its_children_backgrounds(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        position_before = target._background.rect.topleft

        position = tuple_math.add(preadded_widget._background.rect.topleft,
                                  (1, 1))
        preadded_widget.position_at(position)
        ui.update(0.1)

        position_after = target._background.rect.topleft
        assert position_before != position_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_position_at_the_same_position_does_not_move_widget_and_its_children_backgrounds(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        position_before = target._background.rect.topleft

        preadded_widget.position_at(preadded_widget._background.rect.topleft)
        ui.update(0.1)

        position_after = target._background.rect.topleft
        assert position_before == position_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_move_moves_widget_and_its_children_backgrounds(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        position_before = target._background.rect.topleft

        preadded_widget.move((1, 1))
        ui.update(0.1)

        position_after = target._background.rect.topleft
        assert position_before != position_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_move_of_zeros_does_not_move_widget_and_its_children_backgrounds(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        position_before = target._background.rect.topleft

        preadded_widget.move((0, 0))
        ui.update(0.1)

        position_after = target._background.rect.topleft
        assert position_before == position_after


if __name__ == "__main__":
    pg.init()
    screen = create_screen((1280, 720))
    ui = UI(screen)
    keeper = SpriteKeeper(pathlib.Path(__file__).parent)
    panel_builder = PanelBuilder(keeper, "panel_32.png")
    panel = panel_builder.build_panel((640, 480), alpha=True)
    widget = Widget(panel, MockTrigger())
    ui.add(widget, centered=True)

    app = MockApp(screen, ui)
    app.run()
