from pathlib import Path
from sourcefile import CSV, STEP, SourceFile
from slugify import slugify
from csv import QUOTE_NONNUMERIC
import pandas


class Assembly:
    def __init__(self, path: str):
        self.source: SourceFile
        if Path(path).suffix == ".csv":
            self.source = CSV(path)
        if Path(path).suffix == ".step":
            self.source = STEP(path)

        self.name = self.source.assembly.name
        self.sha = ...
        self.msg = ...

        self.parts = self.source.to_parts()

    def export_svg(self):
        DIR = "svg"
        Path(DIR).mkdir(exist_ok=True)
        for part in self.parts:
            part.export_svg(DIR)

    def export_step(self):
        DIR = "step"
        Path(DIR).mkdir(exist_ok=True)
        for part in self.parts:
            part.export_step(DIR)

    def export_assembly_step(self):
        DIR = "step"
        Path(DIR).mkdir(exist_ok=True)
        self.source.assembly.export(f"{DIR}/assembly.step")

    def _to_dataframe(self):
        loc_df = pandas.DataFrame([part.location.__dict__ for part in self.parts])
        rot_df = pandas.DataFrame([part.rotation.__dict__ for part in self.parts])
        dataframe = pandas.DataFrame([part.__dict__ for part in self.parts]).drop(
            ["location", "rotation", "step"], axis=1
        )
        return pandas.concat([dataframe, loc_df, rot_df], axis=1)

    def to_bom(self):
        DIR = Path("doc")
        DIR.mkdir(exist_ok=True)
        df = self._to_dataframe()
        df = (
            df.groupby(["part_name", "part_number", "description"])
            .size()
            .reset_index(name="quantity")
        )
        df["step"] = df.apply(lambda col: slugify(col.part_name) + ".step", axis=1)
        df.to_csv(
            DIR / f"{slugify(self.source.assembly.name)}-bom.csv",
            index=False,
            quoting=QUOTE_NONNUMERIC,
        )

    def to_pnp(self):
        DIR = Path("doc")
        DIR.mkdir(exist_ok=True)
        df = self._to_dataframe()
        df = df.drop("_cq_object", axis=1)
        df.to_csv(
            DIR / f"{slugify(self.source.assembly.name)}-pnp.csv",
            index=False,
            quoting=QUOTE_NONNUMERIC,
        )
