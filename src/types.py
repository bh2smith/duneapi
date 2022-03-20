"""A collection of types associated with Dune Analytics API"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Any

from src.util import datetime_parser


ListInnerResponse = dict[str, list[dict[str, dict[str, str]]]]
DictInnerResponse = dict[str, dict[str, Any]]

DuneRecord = dict[str, str]


@dataclass
class DuneSQLQuery:
    """Contains all the relevant data necessary to initiate a Dune Query"""

    query_id: int
    name: str
    raw_sql: str
    network: Network
    parameters: list[QueryParameter]


# pylint: disable=too-few-public-methods
# TODO - use namedtuple for MetaData and QueryResults
class MetaData:
    """The standard information returned from the Dune API as `query_results`"""

    id: str
    job_id: str
    error: Optional[str]
    runtime: int
    generated_at: datetime
    columns: list[str]

    def __init__(self, obj: str):
        """
        :param obj: input should have the following form
        {
            'id': '3158cc2c-5ed1-4779-b523-eeb9c3b34b21',
            'job_id': '093e440d-66ce-4c00-81ec-2406f0403bc0',
            'error': None,
            'runtime': 0,
            'generated_at': '2022-03-19T07:11:37.344998+00:00',
            'columns': ['number', 'size', 'time', 'block_hash', 'tx_fees'],
            '__typename': 'query_results'
        }
        """
        self.__dict__ = json.loads(obj, object_hook=datetime_parser)


class QueryResults:
    """Class containing the Data results of a Dune Select Query"""

    meta: Optional[MetaData]
    data: list[DuneRecord]

    def __init__(self, data: ListInnerResponse):
        assert data.keys() == {
            "query_results",
            "get_result_by_result_id",
        }, f"invalid keys {data.keys()}"
        assert (
            len(data["query_results"]) == 1
        ), f"Unexpected query_results {data['query_results']}"
        # Could wrap meta conversion into a try-catch, since we don't really need it.
        # But, I can't think of a broad enough exception that won't trip up the liner.
        self.meta = MetaData(json.dumps(data["query_results"][0]))

        self.data = [rec["data"] for rec in data["get_result_by_result_id"]]


class Network(Enum):
    """Enum for supported EVM networks"""

    MAINNET = 4
    GCHAIN = 6

    def __str__(self) -> str:
        match self:
            case Network.MAINNET:
                return "Ethereum mainnet"
            case Network.GCHAIN:
                return "Gnosis chain"
        return super.__str__(self)


class ParameterType(Enum):
    """
    Enum of the 4 distinct dune parameter types
    """

    TEXT = "text"
    NUMBER = "number"
    DATE = "datetime"


class QueryParameter:
    """Class whose instances are Dune Compatible Query Parameters"""

    def __init__(
        self,
        name: str,
        parameter_type: ParameterType,
        value: Any,
    ):
        self.key: str = name
        self.type: ParameterType = parameter_type
        self.value = value

    @classmethod
    def text_type(cls, name: str, value: str) -> QueryParameter:
        """Constructs a Query parameter of type text"""
        return cls(name, ParameterType.TEXT, value)

    @classmethod
    def number_type(cls, name: str, value: int | float) -> QueryParameter:
        """Constructs a Query parameter of type number"""
        return cls(name, ParameterType.NUMBER, value)

    @classmethod
    def date_type(cls, name: str, value: datetime) -> QueryParameter:
        """Constructs a Query parameter of type date"""
        return cls(name, ParameterType.DATE, value)

    def _value_str(self) -> str:
        match self.type:
            case (ParameterType.TEXT):
                return str(self.value)
            case (ParameterType.NUMBER):
                return str(self.value)
            case (ParameterType.DATE):
                # This is the postgres string format of timestamptz
                return str(self.value.strftime("%Y-%m-%d %H:%M:%S"))

        raise TypeError(f"Type {self.type} not recognized!")

    def to_dict(self) -> dict[str, str]:
        """Converts QueryParameter into string json format accepted by Dune API"""
        results = {
            "key": self.key,
            "type": self.type.value,
            "value": self._value_str(),
        }
        return results
