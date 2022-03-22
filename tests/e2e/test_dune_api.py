import unittest

from src.dune_api import DuneAPI
from src.dune_query import DuneQuery
from src.types import Network, QueryParameter


class TestDuneAnalytics(unittest.TestCase):
    def test_interface(self):
        """
        This test indirectly touches all of
        - fetch
        - initiate_new_query
        - execute_and_await_results
        - execute_query
        - post_dune_request
        essentially all the methods of the API
        """
        dune = DuneAPI.new_from_environment()
        five, one = 5, 1
        parameter_name = "IntParameter"
        column_name = "value"
        query = DuneQuery.from_environment(
            # Note that consecutive double brace brackets in formatted strings
            # become single brace brackets, so this query is
            # select 5 - '{{IntParameter}}' as value
            raw_sql=f"select {five} - '{{{{{parameter_name}}}}}' as {column_name}",
            network=Network.MAINNET,
            parameters=[QueryParameter.number_type(parameter_name, one)],
            name="Test Fetch",
        )
        res = dune.fetch(query)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0][column_name], five - one)


if __name__ == "__main__":
    unittest.main()
