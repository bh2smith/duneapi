"""All operations/routes available for interaction with Dune API - looks like graphQL"""
from typing import Collection

from src.types import DuneSQLQuery

PostData = dict[str, Collection[str]]


def find_result_post(result_id) -> PostData:
    """Returns json data to make a post of type FindResultDataByResult"""
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
    return {
        "operationName": "FindResultDataByResult",
        "variables": {"result_id": result_id},
        "query": query,
    }


def get_result_post(query_id: int) -> PostData:
    query = """
    query GetResult($query_id: Int!, $parameters: [Parameter!]) {
      get_result(query_id: $query_id, parameters: $parameters) {
        job_id
        result_id
      }
    }
    """
    return {
        "operationName": "GetResult",
        "variables": {"query_id": query_id},
        "query": query,
    }


def execute_query_post(query_id: int) -> PostData:
    query = """
    mutation ExecuteQuery($query_id: Int!, $parameters: [Parameter!]!) {
      execute_query(query_id: $query_id, parameters: $parameters) {
        job_id
      }
    }
    """
    return {
        "operationName": "ExecuteQuery",
        "variables": {"query_id": query_id, "parameters": []},
        "query": query,
    }


def initiate_query_post(query: DuneSQLQuery) -> PostData:
    object_data = {
        "id": query.query_id,
        "schedule": None,
        "dataset_id": query.network.value,
        "name": query.name,
        "query": query.raw_sql,
        "user_id": 84,
        "description": "",
        "is_archived": False,
        "is_temp": False,
        "tags": [],
        "parameters": [p.to_dict() for p in query.parameters],
        "visualizations": {
            "data": [],
            "on_conflict": {
                "constraint": "visualizations_pkey",
                "update_columns": ["name", "options"],
            },
        },
    }
    return {
        "operationName": "UpsertQuery",
        "variables": {
            "favs_last_24h": False,
            "favs_last_7d": False,
            "favs_last_30d": False,
            "favs_all_time": True,
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
            "session_id": 0,  # This value must be an int, but it doesn't matter what
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
    }
