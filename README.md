# STEPhen - STEP output job automation tool

Copyright (c) 2026 [Antmicro](https://www.antmicro.com)

This is a simple command-line output job automation tool for STEP file assemblies based on `cadquery` library. It allows to decompose a single complex STEP file into sub-parts and generate a mechanical Bill of Materials (BOM) and position files. It also enables recreating complex STEP models from single parts.

## Features

* generation of BoM files containing mechanical components of the assembly in CSV and HTML formats
* generation of PnP-like files containing positions of each mechanical components in 3D space
* exporting assembly components as separate STEP files
* generation of SVG previews of each assembly component
* exporting assembly back from component STEP files and its PnP file

## Installation

While in reposistory, use `pipx` to install `stephen`:

    pipx install .

## Usage

To process an assembly using `stephen`, provide it with a path to a input file (assembly STEP or STEPhen-generated PnP CSV file) and specify output options:

    stephen PATH/TO/INPUT --OPTIONS

Usable options:

    --bom   -b    Export BOM in CSV format      
    --html  -h    Export BOM in HTML format                               
    --pnp   -p    Export PnP in CSV format
    --all   -a    Export entire assembly STEP
    --step  -s    Export STEP files for assembly components
    --svg   -S    Export SVG files for assembly components
     
You can test STEPhen using the model located in `template/` directory:

    stephen template/jetson-agx-thor-baseboard-enclosure.step --step --svg --bom --html --pnp

## License

The `stephen` utility is licensed under the Apache-2.0 [license](LICENSE).
