
from pygame import Surface
from pygame.freetype import Font

from . import shared, tuple_math
from .blueprint import WidgetTrigger
from .imagebox import Imagebox
from .shared import pair
from .textbox import Textbox
from .widget import Widget


class SignedImage(Widget):

    AREA_TO_IMAGE_RATIO = 5

    def __init__(self,
                 bg_texture: Surface,
                 image: Surface | None,
                 text: str,
                 trigger: WidgetTrigger,
                 width_spacing: int,
                 border_size: pair = (0, 0),
                 font: Font | None = None,
                 ) -> None:

        super().__init__(bg_texture, trigger)

        borders = tuple_math.mult(border_size, (2, 2))
        area = tuple_math.sub(bg_texture.get_size(), borders)
        text_start = border_size[0]

        if image is not None:
            ratio = self.AREA_TO_IMAGE_RATIO
            image_area = tuple_math.div(area, (ratio, 1))
            bg = shared.build_transparent_surface(image_area)
            self._imagebox = Imagebox(bg, image, None)
            self.add(self._imagebox)
            self._imagebox.set_offset_base(border_size)

            text_start += image_area[0] + width_spacing

        text_area = (area[0] - text_start + border_size[0],
                     area[1])
        bg = shared.build_transparent_surface(text_area)
        self._textbox = Textbox(
            text, bg, trigger, text_area, font, editable=False, killable=False)
        self.add(self._textbox)
        self._textbox.set_offset_base((text_start, border_size[1]))

    @property
    def offset_base(self) -> pair:
        return self._offset_base

    def set_image(self, new_image: Surface) -> None:
        self._imagebox.set_image(new_image)

    def set_text(self, new_text: str) -> None:
        self._textbox.set_text(new_text)
