from slugify import slugify
from csv import QUOTE_NONNUMERIC
from pathlib import Path
from typing import Literal
from importlib.metadata import version
from jinja2 import Environment, FileSystemLoader
import pandas as pd  # type: ignore[import-untyped]
import logging
import shutil

from stephen.sourcefile import CSV, STEP, SourceFile
from stephen.metadata import Metadata, get_commit_info
from stephen.paths import Paths
import stephen.log as log

logger = logging.getLogger(__name__)

OutputFileFormat = Literal["svg", "step"]


class Assembly:
    """
    Class representing assembly model as Python objects.
    Handles managing the source file parsing and data output exports.
    """

    step_output_dir = Paths.step_output_dir
    svg_output_dir = Paths.svg_output_dir
    doc_output_dir = Paths.doc_output_dir
    html_output_dir = Paths.html_output_dir
    bom_html_temp = Paths.bom_html_temp
    icon_html_temp = Paths.icon_html_temp
    logo_html_temp = Paths.logo_html_temp

    def __init__(self, path: str) -> None:
        self.source: SourceFile
        if Path(path).suffix == ".csv":
            self.source = CSV(path)
        elif Path(path).suffix == ".step":
            self.source = STEP(path)
        else:
            raise FileNotFoundError(f"🔴 Incompatible file format: {path}")

        self.name = self.source.assembly.name
        sha, msg = get_commit_info()
        self._metadata = Metadata(commit_sha=sha, commit_msg=msg, generator="stephen", generator_ver=version("stephen"))

        self.parts = self.source.to_parts()

    def export(self, suffix: OutputFileFormat) -> None:
        """
        Export parts as separate files. Supported file formats are defined in `OutputFileFormat` Literal.
        """
        output_dir = getattr(self, suffix + "_output_dir")
        output_dir.mkdir(exist_ok=True)
        logger.info(f"Exporting {suffix.upper()} files")

        exported_parts = []

        for part in self.parts:
            if part.part_name in exported_parts:
                continue

            getattr(part, "export_" + suffix)(str(output_dir), self._metadata)
            exported_parts.append(part.part_name)

        log.success()

    def export_assembly_step(self) -> None:
        """Export entire assembly to STEP file."""

        self.step_output_dir.mkdir(exist_ok=True)
        path = self.step_output_dir / (slugify(self.name) + ".step")
        logger.info(f"Exporting assembly STEP file")

        self.source.assembly.export(str(path))
        self.source.parser.reload(path)

        self.source.parser.add_metadata(self._metadata)
        self.source.parser.add_properties(parts=self.parts)
        self.source.parser.to_step()

        log.progress(str(path))

    def _to_dataframe(self) -> pd.DataFrame:
        """Convert part data to Pandas dataframe. Splits Location and Rotation into separate vector components."""

        loc_df = pd.DataFrame([part.location.__dict__ for part in self.parts])
        rot_df = pd.DataFrame([part.rotation.__dict__ for part in self.parts])
        df = pd.DataFrame([part.__dict__ for part in self.parts]).drop(["location", "rotation"], axis=1)

        return pd.concat([df, loc_df, rot_df], axis=1)

    def to_bom(self) -> None:
        """Export BOM for the assembly as `*-bom.csv` file."""

        self.doc_output_dir.mkdir(exist_ok=True)
        path = self.doc_output_dir / f"{slugify(self.source.assembly.name)}-bom.csv"

        logger.info(f"Exporting BOM to {path}")

        df = self._to_dataframe()
        df = df.groupby(["part_name", "part_number", "description"]).size().reset_index(name="quantity")
        df["step"] = df.apply(lambda col: slugify(col.part_name) + ".step", axis=1)
        df.to_csv(path, index=False, quoting=QUOTE_NONNUMERIC)

        log.success()

    def to_pnp(self) -> None:
        """Export PnP file for the assembly as `*-pnp.csv` file."""

        self.doc_output_dir.mkdir(exist_ok=True)
        path = self.doc_output_dir / f"{slugify(self.source.assembly.name)}-pnp.csv"

        logger.info(f"Exporting PnP file to {path}")

        df = self._to_dataframe()
        df = df.drop(["_cq_object", "_assembly"], axis=1)
        df.to_csv(path, index=False, quoting=QUOTE_NONNUMERIC)

        log.success()

    def to_html(self) -> None:
        """Export BOM as HTML table."""

        environment = Environment(loader=FileSystemLoader(Paths.template_dir))
        template = environment.get_template(Paths.bom_html_temp)

        self.html_output_dir.mkdir(exist_ok=True)
        shutil.copyfile(Paths.template_dir / Paths.logo_html_temp, self.html_output_dir / Paths.logo_html_temp)
        shutil.copyfile(Paths.template_dir / Paths.icon_html_temp, self.html_output_dir / Paths.icon_html_temp)
        path = self.html_output_dir / f"{slugify(self.source.assembly.name)}-{Paths.bom_html_temp}"

        logger.info(f"Exporting HTML BOM to {path}")

        df = self._to_dataframe()
        df = df.groupby(["part_name", "part_number", "description"]).size().reset_index(name="quantity")
        df["step"] = df.apply(lambda col: slugify(col.part_name) + ".step", axis=1)
        df["svg"] = df.apply(lambda col: slugify(col.part_name) + ".svg", axis=1)

        content = template.render(metadata=self._metadata, parts=df, project_name=self.source.assembly.name)

        with open(path, mode="w", encoding="utf-8") as bom:
            bom.write(content)

        log.success()
