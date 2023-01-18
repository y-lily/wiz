from __future__ import annotations

import pathlib
from typing import Optional
from xml.etree import ElementTree

from src.adventure.animation import Animation
from src.adventure.animation_controller import AnimationController
from src.adventure.camera import AdventureCamera
from src.adventure.entity import MovingEntity
from src.adventure.movement_controller import MovementController
from src.adventure.shared import Path
from src.adventure.sprite_sheet import SpriteSheet


class AdventureHero:

    _camera: AdventureCamera
    _movement_controller: MovementController

    def __init__(self,
                 entity: MovingEntity,
                 camera: Optional[AdventureCamera] = None,
                 ) -> None:

        self._entity = entity
        self._animation_controller = AnimationController(entity)
        if camera is not None:
            self.attach_camera(camera)

    @property
    def entity(self) -> MovingEntity:
        return self._entity

    def attach_camera(self, camera: AdventureCamera) -> None:
        self._camera = camera
        self._movement_controller = MovementController(model=self._entity,
                                                       camera=camera)

    def update(self, dt: float) -> None:
        self._movement_controller.update(dt)
        self._animation_controller.update(dt)

    @staticmethod
    def from_xml_data(data: ElementTree.Element, res_dir: Path) -> AdventureHero:
        res_dir = pathlib.Path(res_dir)
        alpha = data.attrib.get("alpha", False)

        try:
            atlas = SpriteSheet(res_dir / data.attrib["source"], alpha=alpha)
        except KeyError:
            atlas = None

        movement_speed = int(data.attrib["movement_speed"])

        idle_animation = Animation.from_xml_data(data=data.find("idle_animation"),
                                                 res_dir=res_dir,
                                                 atlas=atlas)

        walk_animation = Animation.from_xml_data(data=data.find("walk_animation"),
                                                 res_dir=res_dir,
                                                 atlas=atlas)

        entity = MovingEntity(idle_animation=idle_animation,
                              walk_animation=walk_animation,
                              movement_speed=movement_speed)

        return AdventureHero(entity=entity)

    @staticmethod
    def from_xml_file(path: Path, res_dir: Path) -> AdventureHero:
        tree = ElementTree.parse(path)
        root = tree.getroot()
        return AdventureHero.from_xml_data(root, res_dir)
