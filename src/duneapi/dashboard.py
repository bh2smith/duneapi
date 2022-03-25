"""Dashboard management class"""
from __future__ import annotations

import json

from src.duneapi.api import DuneAPI
from .types import DuneQuery, DashboardTile

BASE_URL = "https://dune.xyz/"


class DuneDashboard:
    """
    A Dune Dashboard consists of a family of queries
    Primary functionality is to update all of them
    without having to manually click refresh.
    """

    name: str
    url: str
    queries: list[DuneQuery]

    def __init__(self, dashboard_conf: str):
        with open(dashboard_conf, "r", encoding="utf-8") as config:
            data = json.loads(config.read())
            meta, queries = data["meta"], data["queries"]
            tiles = [DashboardTile.from_dict(item) for item in queries]

        self.name = meta["name"]
        self.url = meta["url"]
        self.queries = [DuneQuery.from_tile(tile) for tile in tiles]

    def update(self):
        """Creates a dune connection and updates/refreshes all dashboard queries"""
        api = DuneAPI.new_from_environment()
        for tile in self.queries:
            api.initiate_query(tile)
            api.execute_query(tile)

    def __str__(self):
        names = "\n".join(
            f"  {q.name}: {BASE_URL}/queries/{q.query_id}" for q in self.queries
        )
        return f'Dashboard "{self.name}": {self.url}\nQueries:\n{names}'


if __name__ == "__main__":
    dashboard = DuneDashboard("./example/dashboard/my_dashboard.json")
    print(dashboard)
    dashboard.update()
