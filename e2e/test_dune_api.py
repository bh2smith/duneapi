import unittest

from src.dune_analytics import DuneAnalytics, Network, QueryParameter
from src.util import open_query


class TestDuneAnalytics(unittest.TestCase):
    def test_interface(self):
        """
        This test indirectly touches all of
        - fetch
        - initiate_new_query
        - execute_and_await_results
        - execute_query
        - handle_dune_request
        essentially all the methods of the API
        """
        dune = DuneAnalytics.new_from_environment()

        with self.assertRaises(Exception):
            res = dune.fetch(
                query_str=open_query("./e2e/test_query.sql"),
                network=Network.MAINNET,
                parameters=[QueryParameter.number_type("IntParameter", 1)],
            )
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]["value"], 9)


if __name__ == "__main__":
    unittest.main()
