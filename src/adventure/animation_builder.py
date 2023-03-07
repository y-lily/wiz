import pygame as pg
from pygame.surface import Surface

from ..sprites import Animation, SpriteKeeper
from . import shared
from .blueprint import EntityBlueprint
from .shared import Direction


class AnimationBuilder:

    def __init__(self, sprite_keeper: SpriteKeeper):
        self._sprite_keeper = sprite_keeper

    def build(self, entity_def: EntityBlueprint) -> dict[str, Animation]:
        framewidth = entity_def.framewidth
        frameheight = entity_def.frameheight
        alpha = entity_def.alpha
        atlas = self._sprite_keeper.sprite(entity_def.source, alpha)

        sprites = atlas.split((framewidth, frameheight),
                              alpha=alpha)
        framerate = entity_def.framerate
        face_direction = Direction(entity_def.face_direction)

        animations = {}
        for anim, anim_data in entity_def.animations.items():
            frames = {}
            for direction, frames_data in anim_data.items():
                frames[Direction(direction)] = [
                    sprites[i] for i in frames_data.values()]

            if entity_def.flip == "right-left":
                frames |= _flipped_left(frames)
            elif entity_def.flip is None:
                pass
            else:
                shared.assert_never(entity_def.flip)

            animations[anim] = Animation(frames=frames,
                                         frame_rate=framerate,
                                         initial_state=face_direction,
                                         )

        return animations


def _flipped_left(source: dict[Direction, list[Surface]]) -> dict[Direction, list[Surface]]:
    flipped: dict[Direction, list[Surface]] = {}

    supported_directions = {Direction.DOWNRIGHT: Direction.DOWNLEFT,
                            Direction.RIGHT: Direction.LEFT,
                            Direction.UPRIGHT: Direction.UPLEFT}

    for direction, frames in source.items():
        try:
            flipped_direction = supported_directions[direction]
        except KeyError:
            continue

        flipped[flipped_direction] = [
            pg.transform.flip(frame, True, False) for frame in frames]

    return flipped
