import datetime
import json
import unittest

from src.duneapi.types import Network, MetaData, QueryResults, QueryParameter


class TestNetworkEnum(unittest.TestCase):
    def test_string_rep(self):
        self.assertEqual(str(Network.MAINNET), "Ethereum Mainnet")
        self.assertEqual(str(Network.GCHAIN), "Gnosis Chain")
        self.assertEqual(str(Network.SOLANA), "Solana")
        self.assertEqual(str(Network.BINANCE), "Binance Smart Chain")
        self.assertEqual(str(Network.POLYGON), "Polygon")

    def test_try_from_string(self):
        # Mainnet
        self.assertEqual(Network.MAINNET, Network.from_string("mainnet"))
        self.assertEqual(Network.MAINNET, Network.from_string("MaInNet"))
        self.assertEqual(Network.MAINNET, Network.from_string("ethereum mainnet"))
        self.assertEqual(Network.MAINNET, Network.from_string("ETHERIUM MaInNet"))
        self.assertEqual(Network.MAINNET, Network.from_string("MaInNet ethereum"))

        # Gnosis Chain
        self.assertEqual(Network.GCHAIN, Network.from_string("gchain"))
        self.assertEqual(Network.GCHAIN, Network.from_string("Gnosis Chain"))
        self.assertEqual(Network.GCHAIN, Network.from_string("GNOChain"))

        # Binance
        self.assertEqual(Network.BINANCE, Network.from_string("bsc"))
        self.assertEqual(Network.BINANCE, Network.from_string("BSC"))
        self.assertEqual(Network.BINANCE, Network.from_string("Binance"))

        # Optimism
        self.assertEqual(Network.OPTIMISM_V1, Network.from_string("optimism v1"))
        self.assertEqual(Network.OPTIMISM_V2, Network.from_string("optimism v2"))

        # No match!
        with self.assertRaises(ValueError) as err:
            Network.from_string("toot")
        self.assertEqual("could not parse Network from 'toot'", str(err.exception))


class TestQueryResults(unittest.TestCase):
    def setUp(self) -> None:
        self.metadata_content = {
            "id": "3158cc2c-5ed1-4779-b523-eeb9c3b34b21",
            "job_id": "093e440d-66ce-4c00-81ec-2406f0403bc0",
            "error": None,
            "runtime": 0,
            "generated_at": "2022-03-19T07:11:37.344998+00:00",
            "columns": ["number", "size", "time", "block_hash", "tx_fees"],
            "__typename": "query_results",
        }
        self.valid_empty_results = {
            "query_results": [self.metadata_content],
            "get_result_by_job_id": [],
            "query_errors": [],
        }

    def test_metadata_constructor(self):
        result = MetaData(json.dumps(self.metadata_content))
        self.assertEqual(result.__dict__, self.metadata_content)

    def test_constructor_success(self):
        results = QueryResults(self.valid_empty_results)
        self.assertEqual(results.data, [])

    def test_constructor_assertions(self):
        with self.assertRaises(AssertionError) as err:
            QueryResults({"a": [{}]})
        self.assertEqual(str(err.exception), "invalid keys dict_keys(['a'])")

        invalid_query_results = {
            "query_results": [self.metadata_content, {}],  # Not of list type!
            "get_result_by_job_id": [],
            "query_errors": [],
        }
        with self.assertRaises(AssertionError) as err:
            QueryResults(invalid_query_results)
        self.assertEqual(
            str(err.exception),
            f"Unexpected query_results {invalid_query_results}",
        )


class TestQueryParameter(unittest.TestCase):
    def test_constructors_and_to_dict(self):
        number_type = QueryParameter.number_type("Number", 1)
        text_type = QueryParameter.text_type("Text", "hello")
        date_type = QueryParameter.date_type("Date", datetime.datetime(2022, 3, 10))

        self.assertEqual(
            number_type.to_dict(), {"key": "Number", "type": "number", "value": "1"}
        )
        self.assertEqual(
            text_type.to_dict(), {"key": "Text", "type": "text", "value": "hello"}
        )
        self.assertEqual(
            date_type.to_dict(),
            {"key": "Date", "type": "datetime", "value": "2022-03-10 00:00:00"},
        )


if __name__ == "__main__":
    unittest.main()
