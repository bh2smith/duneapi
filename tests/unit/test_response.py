import unittest
from unittest.mock import MagicMock

from requests import Response

from duneapi.response import (
    pre_validate_response,
    validate_and_parse_dict_response,
    validate_and_parse_list_response,
)


class TestOperations(unittest.TestCase):
    def setUp(self) -> None:
        self.response = Response()
        self.key_map = {"x": {"y"}}
        self.valid_dict_data = {"data": {"x": {"y": "z"}}}
        self.valid_list_data = {"data": {"x": [{"y": "z"}]}}

    def test_pre_validation_success(self):
        self.response.status_code = 200
        self.response.json = MagicMock(return_value=self.valid_dict_data)
        response_data = pre_validate_response(self.response, key_map=self.key_map)
        self.assertEqual(response_data, self.valid_dict_data["data"])

    def test_pre_validation_errors(self):
        self.response.status_code = 1
        with self.assertRaises(RuntimeError) as err:
            pre_validate_response(self.response, {})
        self.assertEqual(
            str(err.exception), "('Dune post failed with', <Response [1]>)"
        )

        self.response.status_code = 200
        self.response.json = MagicMock(return_value={"x": {"y": "z"}})
        with self.assertRaises(ValueError) as err:
            pre_validate_response(self.response, key_map={"x": {"y"}})
        self.assertEqual(
            str(err.exception), "response json {'x': {'y': 'z'}} missing 'data' key"
        )

        self.response.json = MagicMock(return_value={"data": {"query_errors": 5}})
        with self.assertRaises(RuntimeError) as err:
            pre_validate_response(self.response, {"x": {"y"}})
        self.assertEqual(str(err.exception), "Dune API Request failed with errors 5")

        self.response.json = MagicMock(return_value=self.valid_dict_data)
        with self.assertRaises(AssertionError) as err:
            pre_validate_response(self.response, key_map={"wrong key": {"y"}})
        self.assertEqual(
            str(err.exception),
            "got=dict_keys(['x']), expected=dict_keys(['wrong key'])",
        )

    def test_dict_validation_success(self):
        self.response.status_code = 200
        self.response.json = MagicMock(return_value=self.valid_dict_data)
        response_data = validate_and_parse_dict_response(
            self.response, key_map=self.key_map
        )
        self.assertEqual(response_data, self.valid_dict_data["data"])

    def test_list_validation_success(self):
        self.response.status_code = 200
        self.response.json = MagicMock(return_value=self.valid_list_data)
        response_data = validate_and_parse_list_response(
            self.response, key_map=self.key_map
        )
        self.assertEqual(response_data, self.valid_list_data["data"])

    def test_dict_validation_error(self):
        self.response.status_code = 200
        # Note that valid list data is not valid dict data
        self.response.json = MagicMock(return_value=self.valid_list_data)
        with self.assertRaises(AssertionError) as err:
            validate_and_parse_dict_response(self.response, key_map=self.key_map)
        self.assertEqual(str(err.exception), "Invalid response type <class 'list'>")

        partially_valid_dict_data = {"data": {"x": {"a": "b"}}}
        self.response.json = MagicMock(return_value=partially_valid_dict_data)
        with self.assertRaises(AssertionError) as err:
            validate_and_parse_dict_response(self.response, key_map=self.key_map)
        self.assertEqual(str(err.exception), "Fail dict_keys(['a']) != {'y'}")

    def test_list_validation_error(self):
        self.response.status_code = 200
        # Note that valid dict data is not valid list data
        self.response.json = MagicMock(return_value=self.valid_dict_data)
        with self.assertRaises(AssertionError) as err:
            validate_and_parse_list_response(self.response, key_map=self.key_map)
        self.assertEqual(str(err.exception), "Invalid response type <class 'dict'>")

        partially_valid_list_data = {"data": {"x": [{"a": "b"}]}}
        self.response.json = MagicMock(return_value=partially_valid_list_data)
        with self.assertRaises(AssertionError) as err:
            validate_and_parse_list_response(self.response, key_map=self.key_map)
        self.assertEqual(str(err.exception), "Fail dict_keys(['a']) != {'y'}")


if __name__ == "__main__":
    unittest.main()
