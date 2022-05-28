import unittest

from src.duneapi.api import DuneAPI
from src.duneapi.types import Network, QueryParameter, DuneQuery


class TestDuneAnalytics(unittest.TestCase):
    def setUp(self) -> None:
        self.five = 5
        self.one = 1
        self.parameter_name = "IntParameter"
        self.column_name = "value"
        self.dune = DuneAPI.new_from_environment()
        self.mainnet_query = self.network_query(Network.MAINNET)

    def network_query(self, network: Network) -> DuneQuery:
        return DuneQuery.from_environment(
            # Note that consecutive double brace brackets in formatted strings
            # become single brace brackets, so this query is
            # select 5 - '{{IntParameter}}' as value
            raw_sql=f"select {self.five} - '{{{{{self.parameter_name}}}}}' as {self.column_name}",
            description="Test Description",
            network=network,
            parameters=[QueryParameter.number_type(self.parameter_name, self.one)],
            name="Test Fetch",
        )

    def test_initiate_query(self):
        self.assertEqual(True, self.dune.initiate_query(self.mainnet_query))

    def test_execute_query(self):
        self.assertNotEqual(None, self.dune.execute_query(self.mainnet_query))

    def test_interface(self):
        """
        This test indirectly touches all of
        - fetch
        - initiate_new_query
        - execute_and_await_results
        - execute_query
        - post_dune_request
        - Tests that the API works on all supported "Networks"
        essentially all the methods of the API
        """
        dune = DuneAPI.new_from_environment()
        for network in Network:
            query = self.network_query(network)
            res = dune.fetch(query)
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0][self.column_name], self.five - self.one)


if __name__ == "__main__":
    unittest.main()
