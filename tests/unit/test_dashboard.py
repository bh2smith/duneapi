import json
import unittest

from src.duneapi.dashboard import DuneDashboard
from src.duneapi.types import DashboardTile, DuneQuery


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.queries = [
            {
                "id": 533353,
                "name": "Example 1",
                "query_file": "./example/dashboard/query1.sql",
                "network": "mainnet",
                "requires": "./example/dashboard/base_query.sql",
            },
            {
                "id": 533351,
                "name": "Example 2",
                "query_file": "./example/dashboard/query2.sql",
                "network": "gchain",
            },
        ]
        self.valid_input = json.loads(
            json.dumps(
                {
                    "meta": {
                        "name": "Test-Dashboard",
                        "url": "bh2smith/Demo-Dashboard",
                    },
                    "queries": self.queries,
                }
            )
        )

    def test_constructor(self):
        dashboard = DuneDashboard.from_json(self.valid_input)
        expected_tiles = [DashboardTile.from_dict(q) for q in self.queries]
        expected_queries = [DuneQuery.from_tile(t) for t in expected_tiles]

        self.assertEqual(dashboard.name, "Test-Dashboard")
        self.assertEqual(dashboard.url, "https://dune.xyzbh2smith/Demo-Dashboard")
        self.assertEqual(dashboard.queries, expected_queries)


if __name__ == "__main__":
    unittest.main()
