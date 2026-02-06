import cadquery as cq
from slugify import slugify
from pathlib import Path
from typing import Dict, List, Tuple, Any
from part import Location, Rotation, Part
from cadquery.occ_impl.geom import Location as CQ_Location
import pandas
import re
import logging

logger = logging.getLogger(__name__)


class SourceFile:
    def __init__(self, path: str) -> None:
        self.path = path
        if not Path(path).is_file():
            raise FileNotFoundError(f"🔴 File not found: {path}")
        logger.info(f"Loading assembly data from: {path}")

        self.assembly: cq.Assembly
        self._data: Any

    def to_parts(self) -> List[Part]:
        pass


class STEP(SourceFile):
    def __init__(self, path: str) -> None:
        super().__init__(path)

        self._load_assembly()
        self._load_data()

    def to_dict(self) -> Dict[str, Any]:
        part_dict = {}
        for part in self.assembly.traverse():
            if part[1].children:
                continue

            # Fusion360 indexing convention stripped here
            part_name = part[1].name.rsplit(":", 1)[0]

            if not self._data.get(part_name):
                continue

            parent_preffix = part[1].parent.name + "/"
            hierarchy = (
                parent_preffix if part[1].parent.name != self.assembly.name else ""
            ) + part[1].name

            entry = {
                part[1].name: {
                    "part_number": self._data.get(part_name)[0],
                    "part_name": self._data.get(part_name)[1],
                    "description": self._data.get(part_name)[2],
                    "parent": part[1].parent.name,
                    "location": Location(*part[1].loc.toTuple()[0]),
                    "rotation": Rotation(*part[1].loc.toTuple()[1]),
                    "hierarchy": hierarchy,
                }
            }

            part_dict.update(entry)
        return part_dict

    def to_parts(self) -> List[Part]:
        logger.info(f"Loading parts")

        return [
            Part(
                ref=part_name,
                **part_dict,
                _cq_object=self.assembly.objects.get(part_dict["hierarchy"]),
            )
            for (part_name, part_dict) in self.to_dict().items()
        ]

    def _load_assembly(self) -> None:
        self.assembly = cq.Assembly().load(self.path)
        logger.info(f"✔ loaded CQ assembly object from {self.path}")

    def _load_data(self) -> None:
        REGEX = (
            r"#[0-9]+=PRODUCT\(\s*(.*?)\s*,\s*(.*?)\s*,\s*(.*?)\s*,\s*\(#[0-9]+\)\s*\)"
        )

        with open(self.path, "r") as step:
            raw_step = step.read().replace("\n", "")

        matches = re.findall(REGEX, raw_step, re.DOTALL)
        matches = [[(item.strip("'\"")) for item in match] for match in matches]
        self._data = {match[1]: match for match in matches}
        logger.info(f"✔ parsed data from {self.path}")


class CSV(SourceFile):
    def __init__(self, path: str) -> None:
        super().__init__(path)

        self._load_data()
        self._load_assembly()

    def to_parts(self) -> List[Part]:
        def load_step(assembly, part_dict):
            DIR = "step"
            path = f"{DIR}/{slugify(part_dict['part_name'])}.step"

            if Path(path).is_file():
                shape = cq.importers.importStep()
            else:
                shape = cq.occ_impl.shapes.Solid(None)

            shape = cq.importers.importStep()
            loc = CQ_Location(
                *part_dict["location"].to_tuple(), *part_dict["rotation"].to_tuple()
            )

            assembly.add(shape, name=part_dict["ref"], loc=loc)
            return assembly.objects.get(part_dict["ref"])

        logger.info(f"Loading parts")

        return [
            Part(**part_dict, _cq_object=load_step(self.assembly, part_dict))
            for part_dict in self.to_dict()
        ]

    def to_dict(self) -> List[Dict[str, Any]]:
        dataframe = self._data
        dataframe["location"] = dataframe.apply(
            lambda row: Location(row["loc_x"], row["loc_y"], row["loc_z"]), axis=1
        )
        dataframe.drop(columns=["loc_x", "loc_y", "loc_z"], inplace=True)

        dataframe["rotation"] = dataframe.apply(
            lambda row: Rotation(row["rot_x"], row["rot_y"], row["rot_z"]), axis=1
        )
        dataframe.drop(columns=["rot_x", "rot_y", "rot_z"], inplace=True)

        return dataframe.to_dict("records")

    def _load_assembly(self) -> None:
        self.assembly = cq.Assembly()
        logger.info(f"✔ created CQ assembly object")

    def _load_data(self) -> None:
        self._data = pandas.read_csv(self.path)
        logger.info(f"✔ parsed data from {self.path}")
