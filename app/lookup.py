import csv
from dataclasses import dataclass
from typing import Dict, List

import requests
from flask import current_app

from app.utils import Regexps, validate


def csv_to_dict(name: str, url: str) -> Dict[str, str]:
    """Create a dict from a csv using the first column as the key and second column as the value."""
    if not url:
        current_app.logger.error(f"{name} csv not found, all lookups will fail.")
        return {}
    content = requests.get(url).text
    reader = csv.reader(content.strip().split("\n"))
    return {serial: name for serial, name, *extra in reader}


@dataclass
class CaseResult:
    case_num: str
    allegations: List[str]
    disposition: str


def find_case(case_num: str) -> CaseResult:
    rows = requests.get(
        f"https://data.seattle.gov/api/id/hyay-5x7b.json?$query=select * where (upper(`file_number`) = upper('{case_num}'))"
    ).json()

    if not rows:
        return None

    allegations = {
        validate(row["allegation"], Regexps.STRING, "Unknown") for row in rows
    }
    disposition = {
        validate(row["disposition"], Regexps.STRING, "Unknown") for row in rows
    }

    return CaseResult(
        case_num,
        list(allegations),
        "".join(disposition) if len(disposition) < 2 else "Partially Sustained",
    )
