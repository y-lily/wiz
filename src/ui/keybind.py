import pygame as pg

from .shared import Direction

BACKSPACE = (pg.K_BACKSPACE,
             )

TAB = (pg.K_TAB,
       )

USE = (pg.K_SPACE,
       )

UP = (pg.K_UP,
      pg.K_KP_8,
      )

DOWN = (pg.K_DOWN,
        pg.K_KP_2,
        )

LEFT = (pg.K_LEFT,
        pg.K_KP_4,
        )

RIGHT = (pg.K_RIGHT,
         pg.K_KP_6,
         )

ESCAPE = (pg.K_ESCAPE,
          )

ZOOM_OUT = (pg.K_MINUS,
            pg.K_KP_MINUS,
            )

ZOOM_IN = (pg.K_EQUALS,
           pg.K_KP_PLUS,
           )

SEND = (pg.K_RETURN,
        pg.K_KP_ENTER,
        )


def key_to_direction(key: int) -> Direction | None:
    return next((direction for bind, direction in keybind_to_direction.items() if key in bind), None)


keybind_to_direction = {
    UP: Direction.UP,
    DOWN: Direction.DOWN,
    LEFT: Direction.LEFT,
    RIGHT: Direction.RIGHT,

}
