import cadquery as cq
from slugify import slugify
from dataclasses import dataclass


class Vector:
    def to_tuple(self):
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

    def export_step(self, dir: str):
        # properties get removed when saving separate step
        self._cq_object.export(f"{dir}/{slugify(self.part_name)}.step")

    def export_svg(self, dir: str) -> None:
        opt = {
            "width": 300,
            "showAxes": False,
            "marginLeft": 10,
            "projectionDir": (0.5, 0.5, 0.5),
            "showHidden": True,
        }
        result = cq.Workplane().newObject([self._cq_object.obj])
        result.export(f"{dir}/{slugify(self.part_name)}.svg", opt=opt)
