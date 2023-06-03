from __future__ import annotations

from contextlib import suppress
from typing import Generic, TypeVar

from typing_extensions import override

from .shared import Direction
from .textbox import Textbox
from .widget import Widget

T = TypeVar("T", bound=object)


class Decorator(Generic[T], object):

    def __init__(self, decorated: T) -> None:
        self._decorated = decorated
        self._decorated_attributes = [x for x in dir(
            decorated) if not x.startswith("__")]

    def __getattr__(self, attribute: str) -> object:
        if attribute in self._decorated_attributes:
            return getattr(self._decorated, attribute)
        with suppress(AttributeError):
            # In case of multiple decorators.
            return getattr(self._decorated._decorated, attribute)
        return getattr(object, attribute)

    def __str__(self) -> str:
        return self._decorated.__str__()

    def undecorated(self) -> T:
        return self._decorated


class WidgetDecorator(Generic[T], Decorator[T]):

    def __getattr__(self, attribute: str) -> object:
        if attribute == "kill":
            return self.kill()
        return super().__getattr__(attribute)

    def kill(self: Widget | Decorator) -> None:
        self._trigger.onKill(self)

        for widget in list(self._decorated._widgets):
            widget.kill()

        self._decorated._widgets = []
        self._decorated._sprites.empty()

        try:
            parent = self._decorated._parent
        except AttributeError:
            return

        # FIXME!!!
        # parent.remove(self._decorated)
        parent.remove(self)


class FadingWidget(WidgetDecorator[Widget]):

    def __init__(self: Widget | FadingWidget,
                 widget: Widget,
                 time_to_fade: float,
                 ) -> None:

        super().__init__(widget)
        self._time_to_fade = time_to_fade

    @override
    def update(self, dt: float) -> None:
        self._decorated.update(dt)

        self._time_to_fade -= dt

        if self._time_to_fade <= 0:
            self.kill()
        else:
            self._show_fade_animation()

    def _show_fade_animation(self) -> None:
        # TODO
        pass


class AutoscrollingTextbox(WidgetDecorator[Textbox]):

    def __init__(self, decorated: Textbox) -> None:
        super().__init__(decorated)

    @override
    def update(self: Textbox | AutoscrollingTextbox, dt: float) -> None:
        self._decorated.update(dt)

        while self._text_sprite.can_scroll(Direction.DOWN):
            self._text_sprite.scroll(Direction.DOWN)


class AnimatedTextbox(WidgetDecorator[Textbox]):

    def __init__(self,
                 textbox: Textbox,
                 animation_speed: float,
                 ) -> None:

        assert animation_speed != 0
        super().__init__(textbox)

        self._entire_text = self._text
        self._decorated.set_text("")
        self._time_passed = 0.0
        self._time_per_letter = 1 / animation_speed

    @override
    def set_text(self, new_text: str) -> None:
        self._decorated.set_text("")
        self._time_passed = 0.0
        self._entire_text = new_text

    @override
    def update(self: Textbox | AnimatedTextbox, dt: float) -> None:
        self._decorated.update(dt)

        # NOTE: Up to optimization, if needed.
        if self._text == self._entire_text:
            return

        self._time_passed += dt
        sign_count = int(self._time_passed // self._time_per_letter)
        self._decorated.set_text(self._entire_text[:sign_count])
