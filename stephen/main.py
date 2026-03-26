from typing import Annotated
import logging
import typer

from stephen.assembly import Assembly
import stephen.log

app = typer.Typer(pretty_exceptions_enable=False)
logger = logging.getLogger(__name__)


@app.command()
def main(
    path: Annotated[str, typer.Argument(help="path to STEP or -pos.csv file")],
    bom: bool = typer.Option(False, "--bom", "-b", help="Export BOM in CSV format"),
    pos: bool = typer.Option(False, "--pos", "-p", help="Export position file in CSV format"),
    step_all: bool = typer.Option(False, "--all", "-a", help="Export entire assembly STEP"),
    step: bool = typer.Option(False, "--step", "-s", help="Export STEP files for assembly components"),
    svg: bool = typer.Option(False, "--svg", "-S", help="Export SVG files for assembly components"),
    html: bool = typer.Option(False, "--html", "-h", help="Export BOM in HTML format"),
) -> None:
    stephen.log.set_logging()
    assembly = Assembly(path)

    if bom:
        assembly.to_bom()
    if pos:
        assembly.to_pos()
    if step_all:
        assembly.export_assembly_step()
    if step:
        assembly.export("step")
    if svg:
        assembly.export("svg")
    if html:
        assembly.to_html()
