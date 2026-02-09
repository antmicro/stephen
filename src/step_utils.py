from pathlib import Path
from typing import Dict, List, Any
import re


def parse_product_data(path: Path) -> Dict[str, List[Any]]:
    REGEX = r"#[0-9]+=PRODUCT\(\s*(.*?)\s*,\s*(.*?)\s*,\s*(.*?)\s*,\s*\(#[0-9]+\)\s*\)"

    with open(path, "r") as step:
        raw_step = step.read().replace("\n", "")

    matches = re.findall(REGEX, raw_step, re.DOTALL)
    matches = [[(item.strip("'\"")) for item in match] for match in matches]
    return {match[1]: match for match in matches}


def prepare_metadata_string(metadata: Dict[str, str], filename: str) -> str:
    return f"""HEADER;
FILE_DESCRIPTION(
/* description */ ('KiCad electronic assembly'),
/* implementation_level */ '2;1');

FILE_NAME(
/* name */ '{filename}',
/* time_stamp */ '{metadata.get("time_stamp")}',
/* author */ ('Antmicro'),
/* commit_sha */ ('{metadata.get("commit_sha")}'),
/* commit_msg */ ('{metadata.get("commit_msg")}'));

FILE_SCHEMA(('AUTOMOTIVE_DESIGN {{ 1 0 10303 214 1 1 1 1 }}'));"""


def add_metadata(path: Path | str, metadata: Dict[str, str]) -> None:
    with open(path, "r") as step:
        raw_step = step.read()

    metadata_str = prepare_metadata_string(metadata, Path(path).name)
    start_line = "HEADER;"
    end_line = "FILE_SCHEMA(('AUTOMOTIVE_DESIGN { 1 0 10303 214 1 1 1 1 }'));"
    REGEX = rf"{re.escape(start_line)}?(.*?){re.escape(end_line)}"

    with open(path, "w") as step:
        step.write(re.sub(REGEX, metadata_str, raw_step, flags=re.DOTALL))
