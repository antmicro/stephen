from pathlib import Path
from sourcefile import CSV, STEP, SourceFile
from slugify import slugify
from csv import QUOTE_NONNUMERIC
import pandas as pd
import logging
from typing import Literal
from paths import Paths
from log import log_success, log_progress
from pathlib import Path
from datetime import datetime, timezone
from typing import Tuple
import git
import step_utils
from importlib.metadata import version


logger = logging.getLogger(__name__)


def get_commit_info() -> Tuple[str, str]:
    try:
        repo = git.Repo(Path.cwd())
        sha, msg = repo.head.object.hexsha, repo.head.object.message.strip()
        logger.info("Current repo Git metadata:")
        logger.info(f"\t · commit SHA: {sha}")
        logger.info(f"\t · commit message: {msg}")
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
        self.metadata_new = {
            "time_stamp": datetime.now(timezone.utc).astimezone().isoformat(),
            "commit_sha": sha,
            "commit_msg": msg,
            "generator_ver": version("stephen"),
        }

        self.parsed_metadata = step_utils.parse_metadata(path)

        self.parts = self.source.to_parts()

    def export(self, suffix=Literal["svg", "step"]) -> None:
        output_dir = self.__getattribute__(suffix + "_output_dir")
        output_dir.mkdir(exist_ok=True)
        logger.info(f"Exporting {suffix.upper()} files")

        exported_parts = []
        for part in self.parts:
            if part.part_name in exported_parts:
                continue
            part.__getattribute__("export_" + suffix)(str(output_dir), self.metadata_new)
            exported_parts.append(part.part_name)
        log_success()

    def export_assembly_step(self) -> None:
        self.step_output_dir.mkdir(exist_ok=True)
        path = f"{self.step_output_dir}/{slugify(self.source.assembly.name)}.step"
        logger.info(f"Exporting assembly STEP file")

        self.source.assembly.export(path)
        step_utils.add_metadata(path, self.metadata_new)
        log_progress(path)

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
