import cadquery as cq
from slugify import slugify
from dataclasses import dataclass
from typing import Tuple
import logging

logger = logging.getLogger(__name__)


class Vector:
    def to_tuple(self) -> Tuple[float, float, float]:
        return tuple(self.__dict__.values())


@dataclass
class Location(Vector):
    loc_x: float
    loc_y: float
    loc_z: float


@dataclass
class Rotation(Vector):
    rot_x: float
    rot_y: float
    rot_z: float


@dataclass
class Part:
    ref: str
    part_number: str
    part_name: str
    description: str
    parent: str
    location: Location
    rotation: Rotation
    hierarchy: str
    _cq_object: cq.Solid

    def export_step(self, dir: str) -> None:
        # properties get removed when saving separate step
        path = f"{dir}/{slugify(self.part_name)}.step"
        self._cq_object.export(path)
        logger.info(f"\t · {path}")

    def export_svg(self, dir: str) -> None:
        opt = {
            "width": 300,
            "showAxes": False,
            "marginLeft": 10,
            "projectionDir": (0.5, 0.5, 0.5),
            "showHidden": True,
        }
        path = f"{dir}/{slugify(self.part_name)}.svg"
        result = cq.Workplane().newObject([self._cq_object.obj])
        result.export(path, opt=opt)
        logger.info(f"\t · {path}")

    def __post_init__(self) -> None:
        logger.info(f"\t · {self.ref}")
