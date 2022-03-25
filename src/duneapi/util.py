"""Utility methods to support Dune API"""
from datetime import datetime
from typing import Any


def postgres_date(date_str: str) -> datetime:
    """Parse a postgres compatible date string into datetime object"""
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S+00:00")


def datetime_parser(dct: dict[str, Any]) -> dict[str, Any]:
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


def open_query(filepath: str) -> str:
    """Opens `filename` and returns as string"""
    with open(filepath, "r", encoding="utf-8") as query_file:
        return query_file.read()
