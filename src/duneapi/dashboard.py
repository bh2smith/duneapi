from __future__ import annotations

import json
from dataclasses import dataclass

from src.duneapi.api import DuneAPI
from .types import DuneQuery, Network
from .util import open_query


@dataclass
class DashboardTile:
    file: str
    query_id: int
    name: str = "Untitled"

    @classmethod
    def from_dict(cls, obj: dict[str, str]) -> DashboardTile:
        """Constructs Record from Dune Data as string dict"""
        return cls(
            file=obj["file"],
            query_id=int(obj["id"]),
        )


class DuneDashboard:
    queries: list[DuneQuery]

    def __init__(self, dashboard_conf: str):
        with open(dashboard_conf, "r") as config:
            tile_json = json.loads(config.read())
            tiles = [DashboardTile.from_dict(item) for item in tile_json]
        queries = [
            DuneQuery(
                name="Untitled",
                raw_sql=open_query(tile.file),
                network=Network.MAINNET,
                parameters=[],
                query_id=tile.query_id,
            )
            for tile in tiles
        ]

        self.queries = queries

    def update(self):
        api = DuneAPI.new_from_environment()
        for tile in self.queries:
            api.initiate_query(tile)
            api.execute_query(tile)


if __name__ == "__main__":
    dashboard = DuneDashboard("./example/dashboard/my_dashboard.json")
    dashboard.update()
