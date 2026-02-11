import cadquery as cq
from slugify import slugify
from dataclasses import dataclass
from typing import Tuple
from pathlib import Path
import logging
from cadquery.occ_impl.geom import Location as CQ_Location
from paths import Paths
from log import log_progress
from parser import STParser
from metadata import Metadata

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
    _assembly: cq.Assembly
    _cq_object: cq.Solid

    def export_step(self, dir: str, metadata: Metadata) -> None:
        path = f"{dir}/{slugify(self.part_name)}.step"
        next(iter(self._cq_object.objects.values())).obj.export(path)

        _parser = STParser(path)
        _parser.add_metadata(metadata)
        _parser.add_properties(part=self)
        _parser.to_step()

        log_progress(path)

    def export_svg(self, dir: str, *args) -> None:
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
        log_progress(path)

    def _load_cq_object(self) -> None:
        if _cq_object := self._assembly.objects.get(self.hierarchy, None):
            self._cq_object = _cq_object
            return

        path = f"{Paths.step_output_dir}/{slugify(self.part_name)}.step"
        if Path(path).is_file():
            shape = cq.importers.importStep(path)
        else:
            shape = cq.Compound.makeCompound([])

        loc = CQ_Location(*self.location.to_tuple(), *self.rotation.to_tuple())

        self._assembly.add(shape, name=self.ref, loc=loc)
        self._cq_object = self._assembly.objects.get(self.ref)

    def __post_init__(self) -> None:
        self._load_cq_object()
        level = "warning" if self._is_compound() else "info"
        log_progress(self.ref, level)

    def _is_compound(self) -> bool:
        return isinstance(next(iter(self._cq_object.objects.values())).obj, cq.Compound)
