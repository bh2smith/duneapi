"""
A collection of types associated with Dune Analytics API.

Includes also, the base classes for a Dune queries, parameters and Request Post Data
All operations/routes available for interaction with Dune API - looks like graphQL
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Collection, Optional

from .util import datetime_parser

PostData = dict[str, Collection[str]]
# key_map = {"outer1": {"inner11", "inner12}, "outer2": {"inner21"}}
KeyMap = dict[str, set[str]]

ListInnerResponse = dict[str, list[dict[str, dict[str, str]]]]
DictInnerResponse = dict[str, dict[str, Any]]

DuneRecord = dict[str, str]


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


@dataclass
class Post:
    """Holds query json and response validation details"""

    data: PostData
    key_map: KeyMap


@dataclass
class DuneQuery:
    """Contains all the relevant data necessary to initiate a Dune Query"""

    name: str
    raw_sql: str
    network: Network
    parameters: list[QueryParameter]
    query_id: int

    @classmethod
    def from_environment(
        cls,
        raw_sql: str,
        network: Network,
        parameters: Optional[list[QueryParameter]] = None,
        name: Optional[str] = None,
    ) -> DuneQuery:
        """Constructs a query using the Universal Query ID provided in env file."""
        return cls(
            raw_sql=raw_sql,
            network=network,
            parameters=parameters if parameters is not None else [],
            name=name if name else "untitled",
            query_id=int(os.environ["DUNE_QUERY_ID"]),
        )

    def _request_parameters(self) -> list[dict[str, str]]:
        return [p.to_dict() for p in self.parameters]

    def initiate_query_post(self) -> Post:
        """Returns json data for a post of type UpsertQuery"""
        object_data: dict[str, Any] = {
            "id": self.query_id,
            "schedule": None,
            "dataset_id": self.network.value,
            "name": self.name,
            "query": self.raw_sql,
            "user_id": 84,
            "description": "",
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
                "private_to_group_id",
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
                  private_to_group_id
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
    def find_result_post(result_id: str) -> Post:
        """Returns json data for a post of type FindResultDataByResult"""
        query = """
        query FindResultDataByResult($result_id: uuid!) {
          query_results(where: { id: { _eq: $result_id } }) {
            id
            job_id
            error
            runtime
            generated_at
            columns
          }
          get_result_by_result_id(args: { want_result_id: $result_id }) {
            data
          }
        }
        """
        return Post(
            data={
                "operationName": "FindResultDataByResult",
                "variables": {"result_id": result_id},
                "query": query,
            },
            key_map={
                "query_results": {
                    "id",
                    "job_id",
                    "error",
                    "runtime",
                    "generated_at",
                    "columns",
                },
                "get_result_by_result_id": {"data"},
            },
        )

    def get_result_post(self) -> Post:
        """Returns json data for a post of type GetResult"""
        query = """
        query GetResult($query_id: Int!, $parameters: [Parameter!]) {
          get_result(query_id: $query_id, parameters: $parameters) {
            job_id
            result_id
          }
        }
        """
        return Post(
            data={
                "operationName": "GetResult",
                "variables": {"query_id": self.query_id},
                "query": query,
            },
            key_map={"get_result": {"job_id", "result_id"}},
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
                "variables": {"query_id": self.query_id, "parameters": []},
                "query": query,
            },
            key_map={"execute_query": {"job_id"}},
        )
