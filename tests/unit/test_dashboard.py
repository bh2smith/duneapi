import json
import unittest

from duneapi.api import DuneAPI
from duneapi.dashboard import DuneDashboard
from duneapi.types import DashboardTile, DuneQuery


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.user = "TestUser"
        self.dune = DuneAPI(username=self.user, password="")
        self.query_path = "./example/dashboard"
        self.queries = [
            {
                "id": 1,
                "name": "Example 1",
                "query_file": "query1.sql",
                "network": "mainnet",
                "requires": "./example/dashboard/base_query.sql",
            },
            {
                "id": 2,
                "name": "Example 2",
                "query_file": "query2-polygon.sql",
                "network": "polygon",
            },
        ]
        self.valid_input = json.loads(
            json.dumps(
                {
                    "meta": {
                        "name": "Demo Dashboard",
                        "user": self.user,
                        "query_path": self.query_path,
                    },
                    "queries": self.queries,
                }
            )
        )

    def test_constructor(self):
        dashboard = DuneDashboard.from_json(self.dune, self.valid_input)
        expected_tiles = [
            DashboardTile.from_dict(q, self.query_path) for q in self.queries
        ]
        expected_queries = [DuneQuery.from_tile(t) for t in expected_tiles]

        self.assertEqual(dashboard.name, "Demo Dashboard")
        self.assertEqual(dashboard.url, f"https://dune.xyz/{self.user}/Demo-Dashboard")
        self.assertEqual(dashboard.queries, expected_queries)

    def test_user_assertion(self):
        minimal_input = {
            "meta": {
                "name": "Demo Dashboard",
                "user": "WrongUser",
            },
            "queries": [],
        }
        # TODO - figure out how to use self.assertLogs
        with self.assertRaises(ValueError) as err:
            DuneDashboard.from_json(self.dune, minimal_input)
        self.assertEqual(
            str(err.exception),
            f"Attempt to load dashboard queries for invalid user WrongUser != {self.user}.",
        )

    def test_duplicate_query(self):
        query_path = "./tests/queries"
        query_file = "test_query.sql"
        minimal_input = {
            "meta": {
                "name": "Demo Dashboard",
                "user": self.user,
                "query_path": query_path,
            },
            "queries": [
                {
                    "id": 1,
                    "name": "Example 1",
                    "query_file": query_file,
                    "network": "gchain",
                },
                {
                    "id": 2,
                    "name": "Example 2",
                    "query_file": query_file,
                    "network": "gchain",
                },
            ],
        }

        with self.assertLogs("duneapi.dashboard", level="WARN") as cm:
            DuneDashboard.from_json(self.dune, minimal_input)
        self.assertEqual(
            cm.output,
            [
                "WARNING:duneapi.dashboard:Duplicate Query Detected [(\"select 10 - '{{IntParameter}}' as value\", <Network.GCHAIN: 6>)]"
            ],
        )


if __name__ == "__main__":
    unittest.main()
