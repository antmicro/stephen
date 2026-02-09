from pathlib import Path
from sourcefile import CSV, STEP, SourceFile
from slugify import slugify
from csv import QUOTE_NONNUMERIC
import pandas as pd
import logging
from typing import Literal
from paths import Paths
from log import log_success

logger = logging.getLogger(__name__)


class Assembly:
    step_output_dir = Paths.step_output_dir
    svg_output_dir = Paths.svg_output_dir
    doc_output_dir = Paths.doc_output_dir

    def __init__(self, path: str) -> None:
        self.source: SourceFile
        if Path(path).suffix == ".csv":
            self.source = CSV(path)
        elif Path(path).suffix == ".step":
            self.source = STEP(path)
        else:
            raise FileNotFoundError(f"🔴 Incompatible file format: {path}")

        self.name = self.source.assembly.name
        self.sha = ...
        self.msg = ...

        self.parts = self.source.to_parts()

    def export(self, suffix=Literal["csv", "step"]) -> None:
        output_dir = self.__getattribute__(suffix + "_output_dir")
        output_dir.mkdir(exist_ok=True)
        logger.info(f"Exporting {suffix.upper()} files")

        exported_parts = []
        for part in self.parts:
            if part.part_name in exported_parts:
                continue
            part.__getattribute__("export_" + suffix)(str(output_dir))
            exported_parts.append(part.part_name)
        log_success()

    def export_assembly_step(self) -> None:
        self.step_output_dir.mkdir(exist_ok=True)
        path = f"{self.step_output_dir}/{self.source.assembly.name}.step"
        logger.info(f"Exporting STEP files")

        self.source.assembly.export(path)
        logger.info(f"\t · {path}")

    def _to_dataframe(self) -> pd.DataFrame:
        loc_df = pd.DataFrame([part.location.__dict__ for part in self.parts])
        rot_df = pd.DataFrame([part.rotation.__dict__ for part in self.parts])
        df = pd.DataFrame([part.__dict__ for part in self.parts]).drop(["location", "rotation"], axis=1)

        return pd.concat([df, loc_df, rot_df], axis=1)

    def to_bom(self) -> None:
        self.doc_output_dir.mkdir(exist_ok=True)
        path = Path(self.doc_output_dir / f"{slugify(self.source.assembly.name)}-bom.csv")
        logger.info(f"Exporting BOM to {path}")

        df = self._to_dataframe()
        df = df.groupby(["part_name", "part_number", "description"]).size().reset_index(name="quantity")
        df["step"] = df.apply(lambda col: slugify(col.part_name) + ".step", axis=1)
        df.to_csv(path, index=False, quoting=QUOTE_NONNUMERIC)
        log_success()

    def to_pnp(self) -> None:
        self.doc_output_dir.mkdir(exist_ok=True)
        path = Path(self.doc_output_dir / f"{slugify(self.source.assembly.name)}-pnp.csv")
        logger.info(f"Exporting PnP file to {path}")

        df = self._to_dataframe()
        df = df.drop(["_cq_object", "_assembly"], axis=1)
        df.to_csv(path, index=False, quoting=QUOTE_NONNUMERIC)
        log_success()
