from __future__ import annotations

from typing import TypeAlias

from ..sprites import SpriteKeeper
from .blueprint import ImageboxBlueprint, Size, TextboxBlueprint
from .decorators import AnimatedTextbox, FadingWidget
from .imagebox import Imagebox
from .textbox import Textbox
from .widget import UI, Widget
from .widget_builder import WidgetBuilder

Coordinate: TypeAlias = Size
Destination: TypeAlias = Coordinate | None
class WidgetLoader:

    def __init__(self, ui: UI, sprite_keeper: SpriteKeeper) -> None:
        self._ui = ui
        self._builder = WidgetBuilder(sprite_keeper)

    def fixed_textbox(self, blueprint: TextboxBlueprint, centered: bool = False, dest: Destination = None) -> Textbox:
        widget = self._builder.build_textbox(blueprint)
        self._attach_to_ui(widget, centered, dest)
        return widget

    def fading_textbox(self, blueprint: TextboxBlueprint, time_to_fade: float, centered: bool = False, dest: Destination = None) -> Textbox | FadingWidget:
        textbox = self._builder.build_textbox(blueprint)
        widget = FadingWidget(textbox, time_to_fade)
        self._attach_to_ui(widget, centered, dest)
        return widget

    def animated_textbox(self, blueprint: TextboxBlueprint, animation_speed: float, centered: bool = False, dest: Destination = None) -> AnimatedTextbox:
        textbox = self._builder.build_textbox(blueprint)
        widget = AnimatedTextbox(textbox, animation_speed)
        self._attach_to_ui(widget, centered, dest)
        return widget

    def imagebox(self, blueprint: ImageboxBlueprint, centered: bool = False, dest: Destination = None) -> Imagebox:
        widget = self._builder.build_imagebox(blueprint)
        self._attach_to_ui(widget, centered, dest)
        return widget

    def _attach_to_ui(self, widget: Widget, centered: bool = False, dest: Destination = None) -> None:
        offset = (dest.x, dest.y) if dest is not None else None
        self._ui.add(widget, centered=centered, offset=offset)
