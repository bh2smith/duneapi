"""Utility methods to support Dune API"""
from datetime import datetime


def datetime_parser(dct):
    """
    Used as object hook in json loads method to parse postgres dates strings
    """
    for key, val in dct.items():
        if isinstance(val, str):
            try:
                dct[key] = datetime.strptime(val, "%Y-%m-%dT%H:%M:%S+00:00")
            except ValueError:
                pass
    return dct
