import unittest
from unittest.mock import MagicMock, Mock

from src.dune_analytics import DuneAnalytics
from src.dune_query import DuneSQLQuery
from src.types import Network


class TestDuneAnalytics(unittest.TestCase):
    def setUp(self) -> None:
        self.dune = DuneAnalytics("user", "password")
        self.query = DuneSQLQuery(
            raw_sql="", network=Network.MAINNET, name="Test", query_id=0, parameters=[]
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

    # TODO - test QueryResult constructor
    # def test_parse_response(self):
    #     sample_response = {
    #         "data": {"get_result_by_result_id": [{"data": {"col1": 1, "col2": 2}}]}
    #     }
    #     expected_result = [{"col1": 1, "col2": 2}]
    #     self.assertEqual(self.dune.parse_response(sample_response), expected_result)


if __name__ == "__main__":
    unittest.main()
