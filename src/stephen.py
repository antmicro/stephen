from assembly import Assembly
from typing import Annotated
import log
import logging
import typer

app = typer.Typer(pretty_exceptions_enable=False)
logger = logging.getLogger(__name__)


@app.command()
def main(
    path: Annotated[str, typer.Argument(help="path to STEP or -pnp.csv file")],
    bom: bool = typer.Option(False, "--bom", "-b", help="Export BOM"),
    pnp: bool = typer.Option(False, "--pnp", "-p", help="Export PnP"),
    step_all: bool = typer.Option(False, "--all", "-a", help="Export entire assembly STEP"),
    step: bool = typer.Option(False, "--step", "-s", help="Export STEP files for assembly components"),
    svg: bool = typer.Option(False, "--svg", "-S", help="Export SVG files for assembly components"),
) -> None:
    log.set_logging()
    assembly = Assembly(path)

    if bom:
        assembly.to_bom()
    if pnp:
        assembly.to_pnp()
    if step_all:
        assembly.export_assembly_step()
    if step:
        assembly.export("step")
    if svg:
        assembly.export("svg")
