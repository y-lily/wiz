from pygame import Surface

from . import tuple_math
from .shared import pair
from .widget import Widget, WidgetSprite, WidgetTrigger


class ProgressBar(Widget):

    def __init__(self,
                 bg: Surface,
                 trigger: WidgetTrigger,
                 empty: Surface,
                 filled: Surface,
                 bar_offset: pair[int] = (0, 0),
                 fill_percent: float = 100.0,
                 ) -> None:

        assert tuple_math.less_or_equal(empty.get_size(),
                                        (bg_size := bg.get_size()))
        assert tuple_math.less_or_equal(filled.get_size(),
                                        bg_size)

        super().__init__(bg, trigger)

        self._fill_percent = fill_percent

        self._progress_sprite = ProgressSprite(empty, filled, fill_percent)
        self._progress_sprite.set_offset_base(bar_offset)
        self._sprites.add(self._progress_sprite)

    @property
    def fill_percent(self) -> float:
        return self._fill_percent

    @fill_percent.setter
    def fill_percent(self, new_value: float) -> None:
        print("calling setter with value", new_value)
        self._fill_percent = new_value
        self._progress_sprite.set_fill_percent(new_value)


class ProgressSprite(WidgetSprite):

    _fill_percent: float

    def __init__(self,
                 empty: Surface,
                 filled: Surface,
                 fill_percent: float,
                 ) -> None:

        assert (empty.get_size() == filled.get_size())

        super().__init__(empty)
        self._filled = WidgetSprite(filled)
        self._sprites.add(self._filled)
        self._bar_width = filled.get_width()

        self.set_fill_percent(fill_percent)

    def set_fill_percent(self, new_value: float) -> None:
        validate_percent(new_value)
        self._fill_percent = new_value
        self._filled.set_offset_base(self._offset_from_percent(new_value))
        print(self._filled._offset_base)

    def _offset_from_percent(self, percent: float) -> pair[int]:
        validate_percent(percent)
        width = self._bar_width
        return (int(width / 100 * percent) - width, 0)


def validate_percent(value: float) -> None:
    if not 0 <= value <= 100:
        raise ValueError(
            f"Expected value to be in the (0, 100) range, got {value} instead.")
