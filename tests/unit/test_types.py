import datetime
import json
import unittest

from src.types import Network, MetaData, QueryResults, QueryParameter


class TestNetworkEnum(unittest.TestCase):
    def test_string_rep(self):
        self.assertEqual(str(Network.MAINNET), "Ethereum mainnet")
        self.assertEqual(str(Network.GCHAIN), "Gnosis chain")


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
            "get_result_by_result_id": [],
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
            "get_result_by_result_id": [],
        }
        with self.assertRaises(AssertionError) as err:
            QueryResults(invalid_query_results)
        self.assertEqual(
            str(err.exception),
            f"Unexpected query_results {invalid_query_results['query_results']}",
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