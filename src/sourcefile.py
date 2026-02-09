import cadquery as cq
from slugify import slugify
from pathlib import Path
from typing import Dict, List, Any
from part import Location, Rotation, Part
from cadquery.occ_impl.geom import Location as CQ_Location
from paths import Paths
import pandas
import re
import logging
from log import log_success
import step_utils

logger = logging.getLogger(__name__)


class SourceFile:
    step_output_dir = Paths.step_output_dir

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        if not self.path.is_file():
            raise FileNotFoundError(f"🔴 File not found: {path}")
        logger.info(f"Loading assembly data from: {path}")

        self.assembly: cq.Assembly
        self._data: Any

    def to_parts(self) -> List[Part]:
        logger.info(f"Loading parts")
        return [Part(**part_dict, _assembly=self.assembly, _cq_object=None) for part_dict in self.to_dict()]

    def to_dict(self) -> List[Dict[str, Any]]:
        return


class STEP(SourceFile):
    def __init__(self, path: str) -> None:
        super().__init__(path)

        self._load_assembly()
        self._load_data()

    def to_dict(self) -> List[Dict[str, Any]]:
        parts = []
        for part in self.assembly.traverse():
            if part[1].children:
                continue

            # Fusion360 indexing convention stripped here
            part_name = part[1].name.rsplit(":", 1)[0]

            if not self._data.get(part_name):
                continue

            parent_preffix = part[1].parent.name + "/"
            hierarchy = (parent_preffix if part[1].parent.name != self.assembly.name else "") + part[1].name

            entry = {
                "ref": part[1].name,
                "part_number": self._data.get(part_name)[0],
                "part_name": self._data.get(part_name)[1],
                "description": self._data.get(part_name)[2],
                "parent": part[1].parent.name,
                "location": Location(*part[1].loc.toTuple()[0]),
                "rotation": Rotation(*part[1].loc.toTuple()[1]),
                "hierarchy": hierarchy,
            }

            parts.append(entry)
        return parts

    def _load_assembly(self) -> None:
        self.assembly = cq.Assembly().load(str(self.path))
        log_success("loaded CQ assembly object from {self.path}")

    def _load_data(self) -> None:
        self._data = step_utils.parse_product_data(self.path)
        log_success("parsed data from {self.path}")


class CSV(SourceFile):
    def __init__(self, path: str) -> None:
        super().__init__(path)

        self._load_data()
        self._load_assembly()

    def to_dict(self) -> List[Dict[str, Any]]:
        df = self._data

        df["location"] = df.apply(lambda row: Location(row["loc_x"], row["loc_y"], row["loc_z"]), axis=1)
        df.drop(columns=["loc_x", "loc_y", "loc_z"], inplace=True)

        df["rotation"] = df.apply(lambda row: Rotation(row["rot_x"], row["rot_y"], row["rot_z"]), axis=1)
        df.drop(columns=["rot_x", "rot_y", "rot_z"], inplace=True)

        return df.to_dict("records")

    def _load_assembly(self) -> None:
        self.assembly = cq.Assembly(name=self.path.stem.rsplit("-", 1)[0])
        log_success("created CQ assembly object")

    def _load_data(self) -> None:
        self._data = pandas.read_csv(self.path)
        log_success("parsed data from {self.path}")
