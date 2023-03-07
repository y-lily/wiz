from os import PathLike
from pathlib import Path
from typing import Any

from .sprite_sheet import SpriteSheet


class SpriteKeeper:

    def __init__(self, resource_dir: PathLike[Any]) -> None:
        self._sprites: dict[Path, SpriteSheet] = {}
        self._resource_dir = Path(resource_dir)

    def sprite(self, relative_path: str, alpha: bool) -> SpriteSheet:
        path = self._resource_dir / relative_path
        try:
            # Don't create a new spritesheet if it's already present.
            return self._sprites[path]
        except KeyError:
            return self._sprites.setdefault(path, SpriteSheet(path, alpha))
