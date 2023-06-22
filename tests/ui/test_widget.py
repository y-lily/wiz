import pathlib
from typing import Any, ClassVar

import pygame as pg
import pytest
from mock_app import MockApp, create_screen
from pygame import Surface
from pytest_lazyfixture import lazy_fixture

# TODO:
# from sprites import SpriteKeeper
# import tuple_math
from src import tuple_math
from src.sprites import SpriteKeeper
from src.ui import UI, FadingWidget, Panel, PanelBuilder, Widget
from src.ui.widget import WidgetTrigger


class TestWidget:

    SCREEN_SIZE: ClassVar = (1280, 720)
    SMALL_PANEL_SIZE: ClassVar = (320, 256)
    PANEL_SIZE: ClassVar = (640, 480)

    @pytest.fixture
    def screen(self) -> Surface:
        return create_screen(self.SCREEN_SIZE)

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
        return panel_builder.build_panel(self.SMALL_PANEL_SIZE, alpha=True)

    @pytest.fixture
    def transparent_panel(self, panel_builder: PanelBuilder) -> Panel:
        return panel_builder.build_panel(self.PANEL_SIZE, alpha=True)

    @pytest.fixture
    def trigger(self) -> WidgetTrigger:
        return WidgetTrigger()

    @pytest.fixture
    def small_widget(self, small_transparent_panel: Panel, trigger: WidgetTrigger) -> Widget:
        return Widget(small_transparent_panel, trigger)

    @pytest.fixture
    def widget(self, transparent_panel: Panel, trigger: WidgetTrigger) -> Widget:
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
    def test_scale_resizes_widgets(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        size_before = target.get_size()

        preadded_widget.scale((1.1, 1.1))
        ui.update(0.1)

        size_after = target.get_size()
        assert size_before != size_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_scale_does_not_resize_widgets_when_given_same_factor(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        size_before = target.get_size()

        preadded_widget.scale((1.0, 1.0))
        ui.update(0.1)

        size_after = target.get_size()
        assert size_before == size_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_ui_scale_resizes_widgets(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        size_before = target.get_size()

        ui.scale((1.1, 1.1))
        ui.update(0.1)

        size_after = target.get_size()
        assert size_before != size_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_ui_scale_does_not_resize_widgets_when_given_same_factor(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        size_before = target.get_size()

        ui.scale((1.0, 1.0))
        ui.update(0.1)

        size_after = target.get_size()
        assert size_before == size_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_set_offset_base_moves_backgrounds(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        position_before = target._bg.rect.topleft

        preadded_widget.set_offset_base((1, 1))
        ui.update(0.1)

        position_after = target._bg.rect.topleft
        assert position_before != position_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_set_offset_base_does_not_move_backgrounds_when_given_same_value(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        position_before = target._bg.rect.topleft

        preadded_widget.set_offset_base((0, 0))
        ui.update(0.1)

        position_after = target._bg.rect.topleft
        assert position_before == position_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_shift_offset_base_moves_backgrounds(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        position_before = target._bg.rect.topleft

        preadded_widget.shift_offset_base((1, 1))
        ui.update(0.1)

        position_after = target._bg.rect.topleft
        assert position_before != position_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_shift_offset_base_does_not_move_backgrounds_when_given_zeros(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        position_before = target._bg.rect.topleft

        preadded_widget.shift_offset_base((0, 0))
        ui.update(0.1)

        position_after = target._bg.rect.topleft
        assert position_before == position_after

    @pytest.mark.parametrize('centered', (True, False))
    def test_setting_centered_moves_backgrounds(self, ui: UI, widget: Widget, centered: bool) -> None:
        ui.add(widget, centered)
        ui.update(0.1)

        position_before = widget._bg.rect.topleft

        widget.centered = not centered
        ui.update(0.1)

        position_after = widget._bg.rect.topleft
        assert position_before != position_after

    @pytest.mark.parametrize('centered', (True, False))
    def test_setting_centered_does_not_move_backgrounds_when_given_same_value(self, ui: UI, widget: Widget, centered: bool) -> None:
        ui.add(widget, centered)
        ui.update(0.1)

        position_before = widget._bg.rect.topleft

        widget.centered = centered
        ui.update(0.1)

        position_after = widget._bg.rect.topleft
        assert position_before == position_after

    @pytest.mark.parametrize('centered', (True, False))
    def test_setting_parent_centered_moves_child_background(self, ui: UI, widget: Widget, small_widget: Widget, centered: bool) -> None:
        ui.add(widget, centered)
        widget.add(small_widget)
        ui.update(0.1)

        position_before = small_widget._bg.rect.topleft

        widget.centered = not centered
        ui.update(0.1)

        position_after = small_widget._bg.rect.topleft
        assert position_before != position_after

    @pytest.mark.parametrize('centered', (True, False))
    def test_setting_parent_centered_does_not_move_child_background_when_given_same_value(self, ui: UI, widget: Widget, small_widget: Widget, centered: bool) -> None:
        ui.add(widget, centered)
        widget.add(small_widget)
        ui.update(0.1)

        position_before = small_widget._bg.rect.topleft

        widget.centered = centered
        ui.update(0.1)

        position_after = small_widget._bg.rect.topleft
        assert position_before == position_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_center_at_moves_backgrounds(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        center_before = target._bg.rect.center

        position = tuple_math.add(preadded_widget._bg.rect.center,
                                  (10, 10))
        preadded_widget.center_at(position)
        ui.update(0.1)

        center_after = target._bg.rect.center
        assert center_before != center_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_center_at_does_not_move_backgrounds_when_given_same_position(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        ui.update(0.1)

        center_before = target._bg.rect.center

        preadded_widget.center_at(preadded_widget._bg.rect.center)
        ui.update(0.1)

        center_after = target._bg.rect.center
        assert center_before == center_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_position_at_moves_backgrounds(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        position_before = target._bg.rect.topleft

        position = tuple_math.add(preadded_widget._bg.rect.topleft,
                                  (1, 1))
        preadded_widget.position_at(position)
        ui.update(0.1)

        position_after = target._bg.rect.topleft
        assert position_before != position_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_position_at_does_not_move_backgrounds_when_given_same_position(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        position_before = target._bg.rect.topleft

        preadded_widget.position_at(preadded_widget._bg.rect.topleft)
        ui.update(0.1)

        position_after = target._bg.rect.topleft
        assert position_before == position_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_move_moves_backgrounds(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        position_before = target._bg.rect.topleft

        preadded_widget.move((1, 1))
        ui.update(0.1)

        position_after = target._bg.rect.topleft
        assert position_before != position_after

    @pytest.mark.parametrize('target', (lazy_fixture('preadded_widget'), lazy_fixture('preadded_child')))
    def test_move_does_not_move_backgrounds_when_given_zeros(self, ui: UI, preadded_widget: Widget, target: Widget) -> None:
        position_before = target._bg.rect.topleft

        preadded_widget.move((0, 0))
        ui.update(0.1)

        position_after = target._bg.rect.topleft
        assert position_before == position_after

    def test_ui_contains_fading_widget(self, ui: UI, widget: Widget) -> None:
        widget = FadingWidget(widget, 10)
        ui.add(widget)

        for _ in range(99):
            ui.update(0.1)

        assert widget in ui._widgets

    def test_fading_widget_is_removed_from_ui_when_time_expires(self, ui: UI, widget: Widget) -> None:
        widget = FadingWidget(widget, 10)
        ui.add(widget)

        for _ in range(101):
            ui.update(0.1)

        assert widget not in ui._widgets

    def test_kill_removes_fading_widget_from_ui(self, ui: UI, widget: Widget) -> None:
        widget = FadingWidget(widget, 10)
        ui.add(widget)

        ui.update(0.1)
        widget.kill()
        ui.update(0.1)

        assert widget not in ui._widgets

    def test_on_use_calls_respective_method_once(self) -> None:
        calls = 0

        def on_use(self: WidgetTrigger, widget: Widget) -> None:
            nonlocal calls
            calls += 1

        trigger = WidgetTrigger(on_use=on_use)
        trigger.onUse(None)
        assert calls == 1

    def test_on_send_calls_respective_method_once(self) -> None:
        calls = 0

        def on_send(self: WidgetTrigger, widget: Widget, data: Any) -> None:
            nonlocal calls
            calls += 1

        trigger = WidgetTrigger(on_send=on_send)
        trigger.onSend(None, None)
        assert calls == 1

    def test_on_send_sends_data(self) -> None:
        received_data = ""

        def on_send(self: WidgetTrigger, widget: Widget, data: Any) -> None:
            nonlocal received_data
            received_data = data

        trigger = WidgetTrigger(on_send=on_send)
        trigger.onSend(None, (sent_data := "sent data"))
        assert received_data == sent_data


if __name__ == "__main__":
    pg.init()
    screen = create_screen((1280, 720))
    ui = UI(screen)
    keeper = SpriteKeeper(pathlib.Path(__file__).parent)
    panel_builder = PanelBuilder(keeper, "panel_32.png")
    panel = panel_builder.build_panel((640, 480), alpha=True)
    widget = Widget(panel, WidgetTrigger())
    ui.add(widget, centered=True)

    app = MockApp(screen, ui)
    app.run()
