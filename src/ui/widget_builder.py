from typing import TypeVar

import pygame as pg
from pygame.color import Color
from pygame.freetype import Font, SysFont

from ..sprites import SpriteKeeper
from ..sprites.sprite_sheet import SpriteSheet
from . import tuple_math
from .blueprint import (
    AtlasBlueprint,
    FontBlueprint,
    ImageboxBlueprint,
    SignedImageBlueprint,
    TextboxBlueprint,
    TextureBlueprint,
    size_to_tuple,
)
from .imagebox import Imagebox
from .signed_image import SignedImage
from .textbox import Textbox
from .texture import Texture, TexturePart

T = TypeVar("T", bound=Textbox)



class WidgetBuilder:

    def __init__(self, sprite_keeper: SpriteKeeper) -> None:
        self._sprite_keeper = sprite_keeper

    def build_textbox(self, blueprint: TextboxBlueprint) -> Textbox:
        texture = self.build_texture(blueprint.texture)
        font = self.build_font(blueprint.font)

        border_size = size_to_tuple(blueprint.texture.part_size)
        text_area_size = tuple_math.sub(texture.get_size(),
                                        tuple_math.mult(border_size, (2, 2)))
        return Textbox(text=blueprint.text,
                    bg_texture=texture,
                    trigger=blueprint.trigger,
                    text_area_size=text_area_size,
                    font=font,
                    editable=blueprint.editable,
                    killable=blueprint.killable,
                    )
    
    def build_imagebox(self, blueprint: ImageboxBlueprint) -> Imagebox:
        texture = self.build_texture(blueprint.texture)
        image = self.build_atlas(blueprint.image).extract_whole()
        return Imagebox(texture, image, blueprint.trigger)

    def build_signed_image(self, blueprint: SignedImageBlueprint) -> SignedImage:
        texture = self.build_texture(blueprint.texture)
        image = self.build_atlas(blueprint.image).extract_whole()
        font = self.build_font(blueprint.font)
        border_size = size_to_tuple(blueprint.texture.part_size)
        return SignedImage(bg_texture=texture,
                           image=image,
                           text=blueprint.text,
                           trigger=blueprint.trigger,
                           width_spacing=blueprint.width_spacing,
                           border_size=border_size,
                           font=font,
                           )

    def build_texture(self, blueprint: TextureBlueprint) -> Texture:
        size = size_to_tuple(blueprint.size)
        part_size = size_to_tuple(blueprint.part_size)
        atlas = self.build_atlas(blueprint)
        sprites = atlas.split(part_size)
        parts = {TexturePart(part): sprites[index]
                 for part, index in blueprint.parts.items()}
        return Texture(size, parts, flags=pg.SRCALPHA)

    def build_font(self, blueprint: FontBlueprint) -> Font:
        font = SysFont(blueprint.name, blueprint.size)
        font.fgcolor = Color(blueprint.color)
        return font
    
    def build_atlas(self, blueprint: AtlasBlueprint) -> SpriteSheet:
        return self._sprite_keeper.sprite(blueprint.source, blueprint.alpha)
