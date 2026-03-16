from pathlib import Path
from typing import List, TypedDict, Any, cast
from abc import ABC, abstractmethod
from slugify import slugify
import pandas as pd  # type: ignore[import-untyped]
import cadquery as cq
import logging

from stephen.part import Location, Rotation, Part
from stephen.parser import STParser
from stephen.paths import Paths
from stephen.metadata import Metadata
import stephen.log as log


logger = logging.getLogger(__name__)


class Data(TypedDict):
    ref: str
    part_number: str
    part_name: str
    description: str
    parent: str
    location: Location
    rotation: Rotation
    hierarchy: str


class SourceFile(ABC):
    """Source file class template for storing assembly and parts data"""

    step_output_dir = Paths.step_output_dir

    def __init__(self, path: str, is_model_based: bool) -> None:
        self.path = Path(path)
        if not self.path.is_file():
            raise FileNotFoundError(f"🔴 File not found: {path}")
        logger.info(f"Loading assembly data from: {path}")

        self.name = self.path.stem.rsplit("-", 1)[0]
        self.parser = (
            STParser(self.path) if is_model_based else STParser(self.step_output_dir / (slugify(self.name) + ".step"))
        )

        self.assembly: cq.Assembly = self._get_assembly()
        self._data = self._get_data()
        self.metadata = self._get_metadata()

    def to_parts(self) -> List[Part]:
        """Return list of `Part()` objects representing components of loaded assembly."""
        logger.info(f"Loading parts")
        return [Part(**part_dict, _assembly=self.assembly, _cq_object=None) for part_dict in self._data]

    def _before_load(self) -> None:
        pass

    @abstractmethod
    def _get_assembly(self) -> cq.Assembly:
        """Return `cq.Assembly` object representing the assembly model"""
        pass

    @abstractmethod
    def _get_data(self) -> List[Data]:
        """Return dictionary containing textual data describing parts of the assembly."""
        pass

    @abstractmethod
    def _get_metadata(self) -> Metadata:
        """Return `Metadata()` object of the entire assembly."""
        pass


class STEP(SourceFile):
    """STEP file format SourceFile class."""

    def __init__(self, path: str, *args: List[Any]) -> None:
        model_based_override = True
        super().__init__(path, model_based_override)

    def _get_assembly(self) -> cq.Assembly:
        log.success(f"loaded CQ assembly object from {self.path}")
        return cq.Assembly().load(str(self.path))

    def _get_data(self) -> List[Data]:
        data = self.parser.get_parts_data()
        parts = []
        for part in self.assembly.traverse():
            if part[1].children:
                continue

            # Fusion360 indexing convention stripped here
            part_name = part[1].name.rsplit(":", 1)[0]
            part_data = data.get(part_name)
            if not part_data:
                continue

            parent_preffix = ""
            parent_name = ""
            if part[1].parent and part[1].parent.name != self.assembly.name:
                parent_preffix = part[1].parent.name + "/"
                parent_name = part[1].parent.name
            hierarchy = parent_preffix + part[1].name

            entry: Data = {
                "ref": part[1].name,
                "part_number": part_data[0],
                "part_name": part_data[1],
                "description": part_data[2],
                "parent": parent_name,
                "location": Location(*part[1].loc.toTuple()[0]),
                "rotation": Rotation(*part[1].loc.toTuple()[1]),
                "hierarchy": hierarchy,
            }

            parts.append(entry)

        log.success(f"parsed data from {self.path}")
        return parts

    def _get_metadata(self) -> Metadata:
        metadata = self.parser.get_metadata()
        logger.info(f"Metadata parsed from {self.path}:")
        for v, k in metadata.items():
            log.progress(f"{v}: {k}")
        return Metadata(**metadata)


class CSV(SourceFile):
    """CSV file format SourceFile class."""

    def __init__(self, path: str, *args: List[Any]) -> None:
        model_based_override = False
        super().__init__(path, model_based_override)

    def _get_assembly(self) -> cq.Assembly:
        log.success("created CQ assembly object")
        return cq.Assembly(name=self.path.stem.rsplit("-", 1)[0])

    def _get_data(self) -> List[Data]:
        df = pd.read_csv(self.path)
        df["location"] = df.apply(lambda row: Location(row["loc_x"], row["loc_y"], row["loc_z"]), axis=1)  # type: ignore[call-overload]
        df.drop(columns=["loc_x", "loc_y", "loc_z"], inplace=True)

        df["rotation"] = df.apply(lambda row: Rotation(row["rot_x"], row["rot_y"], row["rot_z"]), axis=1)  # type: ignore[call-overload]
        df.drop(columns=["rot_x", "rot_y", "rot_z"], inplace=True)

        log.success(f"parsed data from {self.path}")
        data: List[Data] = cast(List[Data], df.to_dict("records"))
        return data

    def _get_metadata(self) -> Metadata:
        """Not yet implemented."""
        return Metadata()
