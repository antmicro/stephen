from pathlib import Path


class Paths:
    """Paths to output directories and template files."""

    step_output_dir: Path = Path("step")
    svg_output_dir: Path = Path("svg")
    doc_output_dir: Path = Path("doc")
    html_output_dir: Path = Path("html")
    template_dir: Path = Path("template")
    bom_html_temp = "bom.html"
    icon_html_temp = "favicon.ico"
    logo_html_temp = "logo.svg"
