"""
A collection of types associated with Dune Analytics API.

Includes also, the base classes for a Dune queries, parameters and Request Post Data
All operations/routes available for interaction with Dune API - looks like graphQL
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Collection, Optional
from web3 import Web3

from dotenv import load_dotenv

from .logger import set_log
from .util import datetime_parser, open_query, postgres_date

log = set_log(__name__)

PostData = dict[str, Collection[str]]
# key_map = {"outer1": {"inner11", "inner12}, "outer2": {"inner21"}}
KeyMap = dict[str, set[str]]

ListInnerResponse = dict[str, list[dict[str, dict[str, str]]]]
DictInnerResponse = dict[str, dict[str, Any]]

DuneRecord = dict[str, str]

# pylint: disable=too-few-public-methods
class Address:
    """
    Class representing Ethereum Address as a hexadecimal string of length 42.
    The string must begin with '0x' and the other 40 characters
    are digits 0-9 or letters a-f. Upon creation (from string) addresses
    are validated and stored in their check-summed format.
    """

    def __init__(self, address: str):
        # Dune uses \x instead of 0x (i.e. bytea instead of hex string)
        # This is just a courtesy to query writers,
        # so they don't have to convert all addresses to hex strings manually
        address = address.replace("\\x", "0x")
        if Address._is_valid(address):
            self.address: str = Web3.toChecksumAddress(address)
        else:
            raise ValueError(f"Invalid Ethereum Address {address}")

    def __str__(self) -> str:
        return str(self.address)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Address):
            return self.address == other.address
        return False

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Address):
            return str(self).lower() < str(other).lower()
        return False

    def __hash__(self) -> int:
        return self.address.__hash__()

    @classmethod
    def zero(cls) -> Address:
        """Returns Null Ethereum Address"""
        return cls("0x0000000000000000000000000000000000000000")

    @classmethod
    def from_int(cls, num: int) -> Address:
        """
        Construct an address from int.
        Used for testing, so that 123 -> "0x0000000000000000000000000000000000000123"
        """
        return cls(f"0x{str(num).rjust(40, '0')}")

    @staticmethod
    def _is_valid(address: str) -> bool:
        match_result = re.match(
            pattern=r"^(0x)?[0-9a-f]{40}$", string=address, flags=re.IGNORECASE
        )
        return match_result is not None


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
        Constructor method
        :param obj: input should have the following form

        Example input:
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
            "get_result_by_job_id",
            "query_errors",
        }, f"invalid keys {data.keys()}"
        assert len(data["query_results"]) == 1, f"Unexpected query_results {data}"
        # Could wrap meta conversion into a try-catch, since we don't really need it.
        # But, I can't think of a broad enough exception that won't trip up the liner.
        self.meta = MetaData(json.dumps(data["query_results"][0]))

        self.data = [rec["data"] for rec in data["get_result_by_job_id"]]


class Network(Enum):
    """Enum for supported EVM networks"""

    SOLANA = 1
    MAINNET = 4
    GCHAIN = 6
    POLYGON = 7
    OPTIMISM_V1 = 8
    BINANCE = 9
    OPTIMISM_V2 = 10

    def __str__(self) -> str:
        result = super.__str__(self)
        if self == Network.SOLANA:
            result = "Solana"
        elif self == Network.MAINNET:
            result = "Ethereum Mainnet"
        elif self == Network.GCHAIN:
            result = "Gnosis Chain"
        elif self == Network.POLYGON:
            result = "Polygon"
        elif self == Network.OPTIMISM_V1:
            result = "Optimism (OVM 1.0)"
        elif self == Network.OPTIMISM_V2:
            result = "Optimism (OVM 2.0)"
        elif self == Network.BINANCE:
            result = "Binance Smart Chain"
        return result

    @classmethod
    def from_string(cls, network_str: str) -> Network:
        """
        Attempts to parse network name from string.
        returns None is no match
        """
        patterns = {
            r"(.*)mainnet": cls.MAINNET,
            r"g(.*)chain": cls.GCHAIN,
            r"solana": cls.SOLANA,
            r"poly": cls.POLYGON,
            r"optimism(.*)1": cls.OPTIMISM_V1,
            r"optimism(.*)2": cls.OPTIMISM_V2,
            r"bsc": cls.BINANCE,
            r"binance": cls.BINANCE,
        }
        for pattern, network in patterns.items():
            if re.match(pattern, network_str, re.IGNORECASE):
                return network
        raise ValueError(f"could not parse Network from '{network_str}'")


class ParameterType(Enum):
    """
    Enum of the 4 distinct dune parameter types
    """

    TEXT = "text"
    NUMBER = "number"
    DATE = "datetime"

    @classmethod
    def from_string(cls, type_str: str) -> ParameterType:
        """
        Attempts to parse Parameter from string.
        returns None is no match
        """
        patterns = {
            r"text": cls.TEXT,
            r"number": cls.NUMBER,
            r"date": cls.DATE,
        }
        for pattern, network in patterns.items():
            if re.match(pattern, type_str, re.IGNORECASE):
                return network
        raise ValueError(f"could not parse Network from '{type_str}'")


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

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, QueryParameter):
            return NotImplemented
        return all(
            [
                self.key == other.key,
                self.value == other.value,
                self.type.value == other.type.value,
            ]
        )

    @classmethod
    def text_type(cls, name: str, value: str) -> QueryParameter:
        """Constructs a Query parameter of type text"""
        return cls(name, ParameterType.TEXT, value)

    @classmethod
    def number_type(cls, name: str, value: int | float) -> QueryParameter:
        """Constructs a Query parameter of type number"""
        return cls(name, ParameterType.NUMBER, value)

    @classmethod
    def date_type(cls, name: str, value: datetime | str) -> QueryParameter:
        """
        Constructs a Query parameter of type date.
        For convenience, we allow proper datetime type, or string
        """
        if isinstance(value, str):
            value = postgres_date(value)
        return cls(name, ParameterType.DATE, value)

    def _value_str(self) -> str:
        if self.type in (ParameterType.TEXT, ParameterType.NUMBER):
            return str(self.value)
        if self.type == ParameterType.DATE:
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

    @classmethod
    def from_dict(cls, obj: dict[str, Any]) -> QueryParameter:
        """
        Constructs Query Parameters from json.
        TODO - this could probably be done similar to the __init__ method of MetaData
        """
        name, value = obj["key"], obj["value"]
        p_type = ParameterType.from_string(obj["type"])
        if p_type == ParameterType.DATE:
            return cls.date_type(name, value)
        if p_type == ParameterType.TEXT:
            assert isinstance(value, str)
            return cls.text_type(name, value)
        if p_type == ParameterType.NUMBER:
            if isinstance(value, str):
                value = float(value) if "." in value else int(value)
            return cls.number_type(name, value)
        raise ValueError(f"Could not parse Query parameter from {obj}")

    def __str__(self) -> str:
        return (
            f"QueryParameter("
            f"name: {self.key}, "
            f"value: {self.value}, "
            f"type: {self.type.value})"
        )


@dataclass
class Post:
    """Holds query json and response validation details"""

    data: PostData
    key_map: KeyMap


@dataclass
class DashboardTile:
    """
    A slightly different arrangement of data that is essentially equivalent to a Query
    Acts as an intermediary type when composing queries from json
    """

    name: str
    description: str
    select_file: str
    query_id: int
    network: Network
    parameters: list[QueryParameter]
    base_file: Optional[str]

    @classmethod
    def from_dict(cls, obj: dict[str, Any], path: str) -> DashboardTile:
        """Constructs Record from Dune Data as string dict"""
        return cls(
            name=obj.get("name", "untitled"),
            description=obj.get("description", ""),
            select_file="/".join([path, obj["query_file"]]),
            network=Network.from_string(obj["network"]),
            query_id=int(obj["id"]),
            parameters=[QueryParameter.from_dict(p) for p in obj.get("parameters", [])],
            base_file=obj.get("requires"),
        )

    def build_query(self) -> str:
        """Constructs a query from base file and select file attributes"""
        if self.base_file is not None:
            components = map(open_query, [self.base_file, self.select_file])
            return "\n".join(list(components))
        return open_query(self.select_file)


@dataclass
class DuneQuery:
    """Contains all the relevant data necessary to initiate a Dune Query"""

    name: str
    description: str
    raw_sql: str
    network: Network
    parameters: list[QueryParameter]
    query_id: int

    def __hash__(self) -> int:
        return hash(self.query_id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DuneQuery):
            return NotImplemented
        equality_conditions = [
            self.name == other.name,
            self.description == other.description,
            self.raw_sql == other.raw_sql,
            self.network.value == other.network.value,
            self.query_id == other.query_id,
            self.parameters == other.parameters,
        ]
        log.debug(f"Equality Conditions: {equality_conditions}")
        return all(equality_conditions)

    @classmethod
    def from_environment(
        cls,
        raw_sql: str,
        network: Network,
        description: str = "",
        parameters: Optional[list[QueryParameter]] = None,
        name: Optional[str] = None,
    ) -> DuneQuery:
        """Constructs a query using the Universal Query ID provided in env file."""
        load_dotenv()
        return cls(
            raw_sql=raw_sql,
            description=description,
            network=network,
            parameters=parameters if parameters is not None else [],
            name=name if name else "untitled",
            query_id=int(os.environ["DUNE_QUERY_ID"]),
        )

    @classmethod
    def from_tile(cls, tile: DashboardTile) -> DuneQuery:
        """Constructs Dune Query from DashboardTile object"""
        return cls(
            name=tile.name,
            description=tile.description,
            raw_sql=tile.build_query(),
            network=tile.network,
            parameters=tile.parameters,
            query_id=tile.query_id,
        )

    def _request_parameters(self) -> list[dict[str, str]]:
        return [p.to_dict() for p in self.parameters]

    def upsert_query_post(self) -> Post:
        """Returns json data for a post of type UpsertQuery"""
        object_data: dict[str, Any] = {
            "id": self.query_id,
            "schedule": None,
            "dataset_id": self.network.value,
            "name": self.name,
            "query": self.raw_sql,
            "user_id": 84,
            "description": self.description,
            "is_archived": False,
            "is_temp": False,
            "tags": [],
            "parameters": self._request_parameters(),
            "visualizations": {
                "data": [],
                "on_conflict": {
                    "constraint": "visualizations_pkey",
                    "update_columns": ["name", "options"],
                },
            },
        }
        key_map = {
            "insert_queries_one": {
                "id",
                "dataset_id",
                "name",
                "description",
                "query",
                "is_private",
                "is_temp",
                "is_archived",
                "created_at",
                "updated_at",
                "schedule",
                "tags",
                "parameters",
                "visualizations",
                "forked_query",
                "user",
                "query_favorite_count_all",
                "favorite_queries",
            }
        }
        return Post(
            data={
                "operationName": "UpsertQuery",
                "variables": {
                    "object": object_data,
                    "on_conflict": {
                        "constraint": "queries_pkey",
                        "update_columns": [
                            "dataset_id",
                            "name",
                            "description",
                            "query",
                            "schedule",
                            "is_archived",
                            "is_temp",
                            "tags",
                            "parameters",
                        ],
                    },
                    "session_id": 0,  # must be an int, but value is irrelevant
                },
                "query": """
                mutation UpsertQuery(
                  $session_id: Int!
                  $object: queries_insert_input!
                  $on_conflict: queries_on_conflict!
                  $favs_last_24h: Boolean! = false
                  $favs_last_7d: Boolean! = false
                  $favs_last_30d: Boolean! = false
                  $favs_all_time: Boolean! = true
                ) {
                  insert_queries_one(object: $object, on_conflict: $on_conflict) {
                    ...Query
                    favorite_queries(where: { user_id: { _eq: $session_id } }, limit: 1) {
                      created_at
                    }
                  }
                }
                fragment Query on queries {
                  ...BaseQuery
                  ...QueryVisualizations
                  ...QueryForked
                  ...QueryUsers
                  ...QueryFavorites
                }
                fragment BaseQuery on queries {
                  id
                  dataset_id
                  name
                  description
                  query
                  is_private
                  is_temp
                  is_archived
                  created_at
                  updated_at
                  schedule
                  tags
                  parameters
                }
                fragment QueryVisualizations on queries {
                  visualizations {
                    id
                    type
                    name
                    options
                    created_at
                  }
                }
                fragment QueryForked on queries {
                  forked_query {
                    id
                    name
                    user {
                      name
                    }
                  }
                }
                fragment QueryUsers on queries {
                  user {
                    ...User
                  }
                }
                fragment User on users {
                  id
                  name
                  profile_image_url
                }
                fragment QueryFavorites on queries {
                  query_favorite_count_all @include(if: $favs_all_time) {
                    favorite_count
                  }
                  query_favorite_count_last_24h @include(if: $favs_last_24h) {
                    favorite_count
                  }
                  query_favorite_count_last_7d @include(if: $favs_last_7d) {
                    favorite_count
                  }
                  query_favorite_count_last_30d @include(if: $favs_last_30d) {
                    favorite_count
                  }
                }
                """,
            },
            key_map=key_map,
        )

    @staticmethod
    def find_result_by_job(job_id: str) -> Post:
        """Returns json data for a post of type FindResultDataByResult"""
        query = """
        query FindResultDataByJob($job_id: uuid!) {
          query_results(where: {job_id: {_eq: $job_id}, error: {_is_null: true}}) {
            id
            job_id
            runtime
            generated_at
            columns
          }
          query_errors(where: {job_id: {_eq: $job_id}}) {
            id
            job_id
            runtime
            message
            metadata
            type
            generated_at
          }
          get_result_by_job_id(args: {want_job_id: $job_id}) {
            data
          }
        }
        """
        return Post(
            data={
                "operationName": "FindResultDataByJob",
                "variables": {"job_id": job_id},
                "query": query,
            },
            key_map={
                "query_results": {
                    "id",
                    "job_id",
                    "runtime",
                    "generated_at",
                    "columns",
                },
                "query_errors": {
                    "id",
                    "job_id",
                    "runtime",
                    "message",
                    "metadata",
                    "type",
                    "generated_at",
                },
                "get_result_by_job_id": {"data"},
            },
        )

    @staticmethod
    def get_queue_position(job_id: str) -> Post:
        """Returns json data for a post of type GetQueuePosition
        This is meant to determine when query execution has completed.
        """
        query = """
        query GetQueuePosition($job_id: uuid!) {
          view_queue_positions(where: {id: {_eq: $job_id}}) {
            pos
          }
          jobs_by_pk(id: $job_id) {
            id
            user_id
            category
            created_at
            locked_until
          }
        }
        """
        return Post(
            data={
                "operationName": "GetQueuePosition",
                "variables": {"job_id": job_id},
                "query": query,
            },
            key_map={"data": {"view_queue_positions", "jobs_by_pk"}},
        )

    def execute_query_post(self) -> Post:
        """Returns json data for a post of type ExecuteQuery"""
        query = """
        mutation ExecuteQuery($query_id: Int!, $parameters: [Parameter!]!) {
          execute_query(query_id: $query_id, parameters: $parameters) {
            job_id
          }
        }
        """
        return Post(
            data={
                "operationName": "ExecuteQuery",
                "variables": {
                    "query_id": self.query_id,
                    "parameters": [p.to_dict() for p in self.parameters],
                },
                "query": query,
            },
            key_map={"execute_query": {"job_id"}},
        )
