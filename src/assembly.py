from pathlib import Path
from sourcefile import CSV, STEP, SourceFile
from slugify import slugify
from csv import QUOTE_NONNUMERIC
import pandas
import logging

logger = logging.getLogger(__name__)


class Assembly:
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

    def export_svg(self) -> None:
        DIR = "svg"
        Path(DIR).mkdir(exist_ok=True)
        logger.info(f"Exporting SVG files")
        exported_parts = []
        for part in self.parts:
            if part.part_name in exported_parts:
                continue
            part.export_svg(DIR)
            exported_parts.append(part.part_name)

    def export_step(self) -> None:
        DIR = "step"
        Path(DIR).mkdir(exist_ok=True)
        logger.info(f"Exporting STEP files")
        exported_parts = []
        for part in self.parts:
            if part.part_name in exported_parts:
                continue
            part.export_step(DIR)
            exported_parts.append(part.part_name)

    def export_assembly_step(self) -> None:
        DIR = "step"
        Path(DIR).mkdir(exist_ok=True)
        logger.info(f"Exporting STEP files")

        path = f"{DIR}/{self.source.assembly.name}.step"
        self.source.assembly.export(path)
        logger.info(f"\t · {path}")

    def _to_dataframe(self) -> pandas.DataFrame:
        loc_df = pandas.DataFrame([part.location.__dict__ for part in self.parts])
        rot_df = pandas.DataFrame([part.rotation.__dict__ for part in self.parts])
        dataframe = pandas.DataFrame([part.__dict__ for part in self.parts]).drop(
            ["location", "rotation"], axis=1
        )
        return pandas.concat([dataframe, loc_df, rot_df], axis=1)

    def to_bom(self) -> None:
        DIR = Path("doc")
        DIR.mkdir(exist_ok=True)
        df = self._to_dataframe()
        df = (
            df.groupby(["part_name", "part_number", "description"])
            .size()
            .reset_index(name="quantity")
        )
        df["step"] = df.apply(lambda col: slugify(col.part_name) + ".step", axis=1)

        logger.info(
            f"Exporting BOM to {DIR / f'{slugify(self.source.assembly.name)}-bom.csv'}"
        )
        df.to_csv(
            DIR / f"{slugify(self.source.assembly.name)}-bom.csv",
            index=False,
            quoting=QUOTE_NONNUMERIC,
        )

    def to_pnp(self) -> None:
        logger.info(f"Generating BOM")
        DIR = Path("doc")
        DIR.mkdir(exist_ok=True)
        df = self._to_dataframe()
        df = df.drop("_cq_object", axis=1)

        logger.info(
            f"Exporting PnP to {DIR / f'{slugify(self.source.assembly.name)}-pnp.csv'}"
        )
        df.to_csv(
            DIR / f"{slugify(self.source.assembly.name)}-pnp.csv",
            index=False,
            quoting=QUOTE_NONNUMERIC,
        )
