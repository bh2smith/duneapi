"""Handles Validation and partial Generic Response Data Parsing"""
from typing import Any

from requests import Response

from .types import ListInnerResponse, DictInnerResponse, KeyMap


def pre_validate_response(response: Response, key_map: KeyMap) -> dict[str, Any]:
    """
    Validates the outermost (generic) part of Dune response data.
    Expects "data" to be a key in the response json and that the
    first level inner keys agree with what the caller expects.
    """
    if response.status_code != 200:
        raise RuntimeError("Dune post failed with", response)

    response_json = response.json()
    if "errors" in response_json.keys() and len(response_json["errors"]) > 0:
        raise RuntimeError(
            f"Dune API Request failed with errors {response_json['errors']}"
        )

    if "data" not in response_json.keys():
        raise ValueError(f"response json {response_json} missing 'data' key")

    query_errors = response_json["data"].get("query_errors")
    if query_errors:
        raise RuntimeError(f"Dune API Request failed with errors {query_errors}")

    response_data: dict[str, Any] = response_json["data"]

    assert (
        response_data.keys() == key_map.keys()
    ), f"got={response_data.keys()}, expected={key_map.keys()}"

    return response_data


def validate_and_parse_dict_response(
    response: Response, key_map: KeyMap
) -> DictInnerResponse:
    """
    Validates responses of dict inner type, and
    returns partially parsed response data
    """
    response_data = pre_validate_response(response, key_map)
    for key, val in key_map.items():
        assert isinstance(
            response_data[key], dict
        ), f"Invalid response type {type(response_data[key])}"
        next_level = response_data[key].keys()
        assert next_level == val, f"Fail {next_level} != {val}"

    return response_data


def validate_and_parse_list_response(
    response: Response, key_map: KeyMap
) -> ListInnerResponse:
    """
    Validates responses with list inner type, and
    returns partially parsed response data
    """
    response_data = pre_validate_response(response, key_map)
    for key, val in key_map.items():
        assert isinstance(
            response_data[key], list
        ), f"Invalid response type {type(response_data[key])}"

        if len(response_data[key]) > 0:
            # Only validate the list if it contains entries
            next_level = response_data[key][0].keys()
            assert next_level == val, f"Fail {next_level} != {val}"

    return response_data
