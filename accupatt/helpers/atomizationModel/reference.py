"""Droplet Spectrum Classification (DSC) reference table and excluded nozzles."""

from __future__ import annotations

DSC_REFERENCE: dict[str, dict] = {
    "VF": {
        "DV01": [0.0, 59.5],
        "DV05": [0.0, 134.4],
        "DV09": [134.4, 236.4],
        "RANK": 0,
        "Color": "#FF0000",
    },
    "F": {
        "DV01": [59.5, 110.3],
        "DV05": [134.4, 248.1],
        "DV09": [236.4, 409.4],
        "RANK": 1,
        "Color": "#FFA500",
    },
    "M": {
        "DV01": [110.3, 162.0],
        "DV05": [248.1, 357.8],
        "DV09": [409.4, 584.0],
        "RANK": 2,
        "Color": "#FFFF00",
    },
    "C": {
        "DV01": [162.0, 191.7],
        "DV05": [357.8, 431.0],
        "DV09": [584.0, 737.1],
        "RANK": 3,
        "Color": "#0000FF",
    },
    "VC": {
        "DV01": [191.7, 226.1],
        "DV05": [431.0, 500.9],
        "DV09": [737.1, 819.8],
        "RANK": 4,
        "Color": "#008000",
    },
    "XC": {
        "DV01": [226.1, 302.5],
        "DV05": [500.9, 658.6],
        "DV09": [819.8, 1142.2],
        "RANK": 5,
        "Color": "#D8D8D8",
    },
    "UC": {
        "DV01": [302.5, 65535],
        "DV05": [658.6, 65535],
        "DV09": [1142.2, 65535],
        "RANK": 6,
        "Color": "#000000",
    },
}

# Nozzles outside the USDA model that still need to appear in selectors
# so users can record their setup. CP01 / CP07 / AccuFlo previously lived here
# but the 2026 model added first-class entries for them.
EXCLUDED_NOZZLES: dict[str, dict] = {
    "CP09A": {
        "Orifice": [0.062, 0.078, 0.125, 0.172],
        "Angle": [30, 55, 90],
    },
    "Micronair": {
        "Orifice": ["AU4000", "AU5000", "AU6539", "AU7000"],
        "Angle": [0],
    },
}
