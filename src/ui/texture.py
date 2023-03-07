from enum import Enum

from pygame.surface import Surface


class TexturePart(Enum):

    TOPLEFT = "topleft"
    TOP = "top"
    TOPRIGHT = "topright"
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    BOTTOMLEFT = "bottomleft"
    BOTTOM = "bottom"
    BOTTOMRIGHT = "bottomright"


class Texture(Surface):
    """A type of surface built from parts (corners, sides and center).
    Like any surface, it is not attached to a specific area of the screen."""

    def __init__(self,
                 size: tuple[int, int],
                 parts: dict[TexturePart, Surface],
                 flags: int = 0,
                 ) -> None:

        # Shortcuts.
        width = size[0]
        height = size[1]
        topleft = parts[TexturePart.TOPLEFT]
        top = parts[TexturePart.TOP]
        topright = parts[TexturePart.TOPRIGHT]
        left = parts[TexturePart.LEFT]
        center = parts[TexturePart.CENTER]
        right = parts[TexturePart.RIGHT]
        botleft = parts[TexturePart.BOTTOMLEFT]
        bot = parts[TexturePart.BOTTOM]
        botright = parts[TexturePart.BOTTOMRIGHT]

        # The border parts have to match to be drawn nicely.
        # NOTE: The code which works with unmatching border parts is replaced as it does not have any
        # practical use and is much more difficult to read and maintain.
        assert topleft.get_height() == top.get_height() == topright.get_height()
        assert left.get_height() == center.get_height() == right.get_height()
        assert botleft.get_height() == bot.get_height() == botright.get_height()

        assert topleft.get_width() == left.get_width() == botleft.get_width()
        assert top.get_width() == center.get_width() == bot.get_width()
        assert topright.get_width() == right.get_width() == botright.get_width()

        # Make sure the center surface covers everything corners and sides don't.
        left_border_width = topleft.get_width()
        right_border_width = topright.get_width()
        top_border_height = topleft.get_height()
        bot_border_height = botleft.get_height()

        # Shrink the size to avoid overlapping of the parts.
        inner_width = width - (left_border_width + right_border_width)
        extra_width = inner_width % center.get_width()
        inner_height = height - (bot_border_height + top_border_height)
        extra_height = inner_height % center.get_height()
        if extra_width or extra_height:
            print(f"A texture with a suggested size {width}x{height} will be resized "
                  f"to {width-extra_width}x{height-extra_height} to avoid parts overlapping.")
        width -= extra_width
        height -= extra_height

        super().__init__(size=(width, height), flags=flags)

        start_x = left_border_width
        start_y = top_border_height
        end_x = width - right_border_width
        end_y = height - bot_border_height

        # Blit the center.
        self.blits([(center, (x, y))
                    for x in range(start_x, end_x, center.get_width())
                    for y in range(start_y, end_y, center.get_height())])

        # Blit the sides.
        self.blits([(left, (0, y))
                   for y in range(start_y, end_y, left.get_height())])
        self.blits([(right, (end_x, y))
                   for y in range(start_y, end_y, right.get_height())])
        self.blits([(top, (x, 0))
                   for x in range(start_x, end_x, top.get_width())])
        self.blits([(bot, (x, end_y))
                   for x in range(start_x, end_x, bot.get_width())])

        # Blit the corners.
        self.blit((topleft), (0, 0))
        self.blit(topright, (end_x, 0))
        self.blit(botleft, (0, end_y))
        self.blit(botright, (end_x, end_y))
