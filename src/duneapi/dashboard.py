"""Dashboard management class"""
from __future__ import annotations

import json
from typing import Any

from .api import DuneAPI
from .types import DuneQuery, DashboardTile

BASE_URL = "https://dune.xyz"


class DuneDashboard:
    """
    A Dune Dashboard consists of a family of queries
    Primary functionality is to update all of them
    without having to manually click refresh.
    """

    name: str
    url: str
    queries: list[DuneQuery]

    def __init__(self, name: str, handle: str, tiles: list[DashboardTile]):
        # Tile Validation
        assert len(set(t.query_id for t in tiles)) == len(tiles), "Duplicate query ID"
        assert len(set(t.select_file for t in tiles)) == len(tiles), "Duplicate query"

        self.name = name
        self.url = BASE_URL + handle
        self.queries = [DuneQuery.from_tile(tile) for tile in tiles]

    @classmethod
    def from_file(cls, filename: str) -> DuneDashboard:
        """Constructs Dashboard from configuration file"""
        with open(filename, "r", encoding="utf-8") as config:
            data = json.loads(config.read())
        return cls.from_json(data)

    @classmethod
    def from_json(cls, json_obj: dict[str, Any]) -> DuneDashboard:
        """Constructs Dashboard from json file"""
        meta, queries = json_obj["meta"], json_obj["queries"]
        tiles = [DashboardTile.from_dict(q) for q in queries]
        return cls(name=meta["name"], handle=meta["url"], tiles=tiles)

    def update(self) -> None:
        """Creates a dune connection and updates/refreshes all dashboard queries"""
        api = DuneAPI.new_from_environment()
        for tile in self.queries:
            api.initiate_query(tile)
            api.execute_query(tile)

    def __str__(self) -> str:
        names = "\n".join(
            f"  {q.name}: {BASE_URL}/queries/{q.query_id}" for q in self.queries
        )
        return f'Dashboard "{self.name}": {self.url}\nQueries:\n{names}'


if __name__ == "__main__":
    dashboard = DuneDashboard.from_file("./example/dashboard/my_dashboard.json")
    dashboard.update()
    print("Updated", dashboard)
