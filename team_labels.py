from __future__ import annotations

TEAM_LABELS = {
    "TID": "ALP",
    "MB4": "BRV",
    "DTU": "CRN",
    "QSS": "DLS",
    "I2A": "EVK",
    "SMW": "FQM",
    "SMH": "GTR",
    "MNG": "HZN",
}


def team_label(team_code: str) -> str:
    return TEAM_LABELS.get(str(team_code), str(team_code))
