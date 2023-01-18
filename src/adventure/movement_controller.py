import pygame
from statemachine import State, StateMachine

from src.adventure.camera import AdventureCamera
from src.adventure.entity import MovingEntity


class MovementTypeChanged(Exception):
    pass


class MovementState(State):

    def post_init(self,
                  model: MovingEntity,
                  camera: AdventureCamera,
                  ) -> None:

        self._model = model
        self._camera = camera

    def update(self, dt: float) -> None:
        pressed = pygame.key.get_pressed()

        if pressed[pygame.K_UP]:
            face_direction = "up"
            self._model.velocity[1] = -self._model.movement_speed
        elif pressed[pygame.K_DOWN]:
            face_direction = "down"
            self._model.velocity[1] = self._model.movement_speed
        else:
            face_direction = ""
            self._model.velocity[1] = 0

        if pressed[pygame.K_LEFT]:
            face_direction += "left"
            self._model.velocity[0] = -self._model.movement_speed
        elif pressed[pygame.K_RIGHT]:
            face_direction += "right"
            self._model.velocity[0] = self._model.movement_speed
        else:
            face_direction += ""
            self._model.velocity[0] = 0

        if face_direction != "":
            self._model.face_direction = face_direction

        self._handle_collisions()

    def _is_moving(self) -> bool:
        return any([self._model.velocity[0] != 0,
                   self._model.velocity[1] != 0])

    def _handle_collisions(self) -> None:
        if self._model.find_collision(self._camera.collision_zones) > -1:
            self._model.to_last_stable_ground()


class IdleState(MovementState):

    def post_init(self,
                  model: MovingEntity,
                  camera: AdventureCamera,
                  ) -> None:

        super().post_init(model, camera)

    def update(self, dt: float) -> None:
        super().update(dt)
        if self._is_moving():
            # self._model.movement_state = "walking"
            raise MovementTypeChanged


class WalkState(MovementState):

    def post_init(self,
                  model: MovingEntity,
                  camera: AdventureCamera,
                  ) -> None:

        super().post_init(model, camera)

    def update(self, dt: float) -> None:
        super().update(dt)
        if not self._is_moving():
            # self._model.movement_state = "idle"
            raise MovementTypeChanged


class MovementController(StateMachine):

    idle = IdleState("Idle", initial=True)
    walking = WalkState("Walking")

    change_movement_type = idle.to(walking) | walking.to(idle)

    def __init__(self,
                 model: MovingEntity,
                 camera: AdventureCamera,
                 start_value: str = "idle",
                 ) -> None:

        super().__init__(model,
                         state_field="movement_state",
                         start_value=start_value)

        self.idle.post_init(model=self.model, camera=camera)
        self.walking.post_init(model=self.model, camera=camera)

    def on_enter_state(self, source: MovementState, state: MovementState) -> None:
        pass

    def update(self, dt: float) -> None:
        try:
            self.current_state.update(dt)
        except MovementTypeChanged:
            self.change_movement_type()
