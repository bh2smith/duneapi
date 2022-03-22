"""
The Base class for a Dune Query, along with Request Post Data
All operations/routes available for interaction with Dune API - looks like graphQL"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Collection, Optional

from src.types import Network, QueryParameter

PostData = dict[str, Collection[str]]
# key_map = {"outer1": {"inner11", "inner12}, "outer2": {"inner21"}}
KeyMap = dict[str, set[str]]


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
