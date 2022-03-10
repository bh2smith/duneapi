import unittest
from unittest.mock import MagicMock, Mock

from src.dune_analytics import DuneAnalytics, Network


class TestNetworkEnum(unittest.TestCase):
    def test_string_rep(self):
        self.assertEqual(str(Network.MAINNET), "Ethereum mainnet")
        self.assertEqual(str(Network.GCHAIN), "Gnosis chain")


class TestDuneAnalytics(unittest.TestCase):

    def setUp(self) -> None:
        self.dune = DuneAnalytics('user', 'password', 0)

    def test_retry(self):
        self.dune.execute_and_await_results = MagicMock(return_value=1)
        self.dune.initiate_new_query = MagicMock(return_value=None)
        self.dune.open_query = MagicMock(return_value="")

        with self.assertRaises(Exception):
            self.dune.query_initiate_execute_await(
                query_filepath="",
                network=Network.MAINNET,
                max_retries=0
            )

        self.assertEqual(
            self.dune.query_initiate_execute_await(
                query_filepath="",
                network=Network.MAINNET,
                max_retries=1
            ), 1)

        self.dune.execute_and_await_results = Mock(side_effect=Exception("Max retries"))
        with self.assertRaises(Exception):
            self.dune.query_initiate_execute_await(
                query_filepath="",
                network=Network.MAINNET,
                max_retries=2
            )

    def test_parse_response(self):
        sample_response = {
            "data": {
                "get_result_by_result_id": [
                    {
                        "data": {
                            "col1": 1,
                            "col2": 2
                        }
                    }
                ]
            }
        }
        expected_result = [
            {
                "col1": 1,
                "col2": 2
            }
        ]
        self.assertEqual(self.dune.parse_response(sample_response), expected_result)


if __name__ == '__main__':
    unittest.main()
