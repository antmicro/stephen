from slugify import slugify
from csv import QUOTE_NONNUMERIC
from pathlib import Path
from typing import Tuple, Literal
from importlib.metadata import version
import pandas as pd
import git
import logging
from jinja2 import Environment, FileSystemLoader

from stephen.sourcefile import CSV, STEP, SourceFile
from stephen.metadata import Metadata
from stephen.parser import STParser
from stephen.paths import Paths
import stephen.log as log

logger = logging.getLogger(__name__)


def get_commit_info() -> Tuple[str, str]:
    try:
        repo = git.Repo(Path.cwd())
        sha, msg = repo.head.object.hexsha, repo.head.object.message.strip()
        logger.info("Current repo Git metadata:")
        log.progress(f"commit SHA: {sha}")
        log.progress(f"commit message: {msg}")
        return sha, msg
    except git.exc.InvalidGitRepositoryError:
        logger.warning(
            "Current workdir doesn't seem to be a Git repository, passing empty commit message and SHA strings!"
        )
        return "$", "$"


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
        sha, msg = get_commit_info()
        self._metadata = Metadata(commit_sha=sha, commit_msg=msg, generator="stephen", generator_ver=version("stephen"))

        self.parts = self.source.to_parts()

    def export(self, suffix=Literal["svg", "step"]) -> None:
        output_dir = self.__getattribute__(suffix + "_output_dir")
        output_dir.mkdir(exist_ok=True)
        logger.info(f"Exporting {suffix.upper()} files")

        exported_parts = []
        for part in self.parts:
            if part.part_name in exported_parts:
                continue
            part.__getattribute__("export_" + suffix)(str(output_dir), self._metadata)
            exported_parts.append(part.part_name)
        log.success()

    def export_assembly_step(self) -> None:
        self.step_output_dir.mkdir(exist_ok=True)
        path = f"{self.step_output_dir}/{slugify(self.source.assembly.name)}.step"
        logger.info(f"Exporting assembly STEP file")

        self.source.assembly.export(path)

        parser = self.source._parser if isinstance(self, STEP) else STParser(path)
        parser.add_metadata(self._metadata)
        parser.add_properties(parts=self.parts)
        parser.to_step()

        log.progress(path)

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
        log.success()

    def to_pnp(self) -> None:
        self.doc_output_dir.mkdir(exist_ok=True)
        path = Path(self.doc_output_dir / f"{slugify(self.source.assembly.name)}-pnp.csv")
        logger.info(f"Exporting PnP file to {path}")

        df = self._to_dataframe()
        df = df.drop(["_cq_object", "_assembly"], axis=1)
        df.to_csv(path, index=False, quoting=QUOTE_NONNUMERIC)
        log.success()

    def to_html(self) -> None:
        environment = Environment(loader=FileSystemLoader(Paths.template_dir))
        template = environment.get_template(Paths.bom_html_temp)

        self.doc_output_dir.mkdir(exist_ok=True)
        path = Path(self.doc_output_dir / f"{slugify(self.source.assembly.name)}-bom.html")
        logger.info(f"Exporting HTML BOM to {path}")

        df = self._to_dataframe()
        df = df.groupby(["part_name", "part_number", "description"]).size().reset_index(name="quantity")
        df["step"] = df.apply(lambda col: slugify(col.part_name) + ".step", axis=1)
        df["svg"] = df.apply(lambda col: slugify(col.part_name) + ".svg", axis=1)

        content = template.render(metadata=self._metadata, parts=df, project_name=self.source.assembly.name)

        with open(path, mode="w", encoding="utf-8") as bom:
            bom.write(content)
        log.success()
