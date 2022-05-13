import re


class Regexps:
    CASE_NUM = "\\d{4}OPA-\\d{4}"
    CCS_DISPOSITION = "((No|All) Allegations Sustained|Partially Sustained|-)"
    CCS_URL = "https://www.seattle.gov/Documents/Departments/OPA/ClosedCaseSummaries/\\d{4}OPA-\\d{4}ccs\\d{4,10}.pdf"
    SERIAL = "\\d{1,4}"
    STRING = "[\\w \\-,]{1,255}"
    TIMESTAMP = "\\d{4}(-\\d{2}){2}T\\d{2}(:\\d{2}){2}(.\\d{3})?"


def validate(s, pattern, default) -> str:
    """Try to validate a string against a pattern and returns a default value if validation fails."""
    return s if re.match(f"^{pattern}$", s) else default
