import unittest
from unittest.mock import MagicMock, Mock

from duneapi.api import DuneAPI
from duneapi.types import DuneQuery, Network


class TestDuneAnalytics(unittest.TestCase):
    def setUp(self) -> None:
        self.dune = DuneAPI("user", "password")
        self.query = DuneQuery(
            raw_sql="",
            description="",
            network=Network.MAINNET,
            query_id=0,
            parameters=[],
            name="Test",
        )

    def test_retry(self):
        self.dune.execute_and_await_results = MagicMock(return_value=1)
        self.dune.initiate_query = MagicMock(return_value=None)
        self.dune.open_query = MagicMock(return_value="")
        self.dune.max_retries = 0
        with self.assertRaises(Exception):
            self.dune.fetch(self.query)

        self.dune.max_retries = 1
        self.assertEqual(self.dune.fetch(self.query), 1)

        self.dune.execute_and_await_results = Mock(side_effect=Exception("Max retries"))
        with self.assertRaises(Exception):
            self.dune.fetch(self.query)


if __name__ == "__main__":
    unittest.main()
