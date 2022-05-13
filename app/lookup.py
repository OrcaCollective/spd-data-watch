import csv
from dataclasses import dataclass
from typing import Dict, List

import requests
from flask import current_app

from app.utils import Regexps, validate


def csv_to_dict(url: str) -> Dict[str, str]:
    """Create a dict from a csv using the first column as the key and second column as the value."""
    content = requests.get(url).text
    reader = csv.reader(content.strip().split("\n"))
    return {serial: name for serial, name, *extra in reader}


uid_map = csv_to_dict(current_app.config["UID_CSV_URL"])
roster_map = csv_to_dict(current_app.config["ROSTER_CSV_URL"])


def find_serial(uid: str) -> str:
    return uid_map.get(uid, "Unknown")


def find_name(serial: str) -> str:
    return roster_map.get(serial, "Unknown")


@dataclass
class CaseResult:
    case_num: str
    officers: List[str]
    allegations: List[str]
    disposition: str


def find_case(case_num: str) -> CaseResult:
    rows = requests.get(
        f"https://data.seattle.gov/api/id/99yi-dthu.json?$query=select * where (upper(`file_number`) = upper('{case_num}'))"
    ).json()

    if not rows:
        return None

    officers = {
        validate(row["named_employee_id"], Regexps.SERIAL, "Unknown") for row in rows
    }
    allegations = {
        validate(row["allegation"], Regexps.STRING, "Unknown") for row in rows
    }
    disposition = {
        validate(row["disposition"], Regexps.STRING, "Unknown") for row in rows
    }

    return CaseResult(
        case_num,
        officers,
        list(allegations),
        "".join(disposition) if len(disposition) < 2 else "Partially Sustained",
    )
