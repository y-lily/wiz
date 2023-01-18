from src.adventure.animation import Animation
from src.adventure.entity import MovingEntity
from src.adventure.shared import Direction
from lib.assert_never import assert_never


class AnimationController:

    _entity: MovingEntity
    _animation: Animation
    _frame: float
    _last_movement_state: str

    def __init__(self,
                 entity: MovingEntity,
                 ) -> None:

        self._entity = entity
        movement_state = self._get_movement_state()
        self._load_movement_state(movement_state)

    def update(self, dt: float) -> None:
        movement_state = self._get_movement_state()
        if movement_state != self._last_movement_state:
            self._load_movement_state(movement_state)

        face_direction = self._entity.face_direction
        self._animation.state = Direction(face_direction)
        self._animation.update(dt)
        self._entity.image = self._animation.get_image()

    def _get_movement_state(self) -> str:
        return self._entity.movement_state

    def _load_movement_state(self, movement_state: str) -> None:
        if movement_state == "idle":
            self._animation = self._entity.idle_animation
        elif movement_state == "walking":
            self._animation = self._entity.walk_animation
        else:
            assert_never(movement_state)

        self._last_movement_state = movement_state
        self._frame = 0
