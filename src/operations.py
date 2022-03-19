from typing import Collection

PostData = dict[str, Collection[str]]


def find_result_post(result_id) -> PostData:
    return {
        "operationName": "FindResultDataByResult",
        "variables": {"result_id": result_id},
        "query": "query FindResultDataByResult($result_id: uuid!) "
        "{\n  query_results(where: {id: {_eq: $result_id}}) "
        "{\n    id\n    job_id\n    error\n    runtime\n    "
        "generated_at\n    columns\n    __typename\n  }"
        "\n  get_result_by_result_id(args: {want_result_id: $result_id}) "
        "{\n    data\n    __typename\n  }\n}\n",
    }


def get_result_post(query_id: int) -> PostData:
    return {
        "operationName": "GetResult",
        "variables": {"query_id": query_id},
        "query": "query GetResult($query_id: Int!, $parameters: [Parameter!]) "
        "{\n  get_result(query_id: $query_id, parameters: $parameters) "
        "{\n    job_id\n    result_id\n    __typename\n  }\n}\n",
    }


def execute_query_post(query_id: int) -> PostData:
    return {
        "operationName": "ExecuteQuery",
        "variables": {"query_id": query_id, "parameters": []},
        "query": "mutation ExecuteQuery($query_id: Int!, $parameters: [Parameter!]!)"
        "{\n  execute_query(query_id: $query_id, parameters: $parameters) "
        "{\n    job_id\n    __typename\n  }\n}\n",
    }


def initiate_query_post() -> PostData:
    object_data = {
        "id": self.query_id,
        "schedule": None,
        "dataset_id": network.value,
        "name": name,
        "query": query,
        "user_id": 84,
        "description": "",
        "is_archived": False,
        "is_temp": False,
        "tags": [],
        "parameters": [p.to_dict() for p in parameters],
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
            "session_id": 84,
        },
        # pylint: disable=line-too-long
        "query": "mutation UpsertQuery($session_id: Int!, $object: queries_insert_input!, $on_conflict: queries_on_conflict!, $favs_last_24h: Boolean! = false, $favs_last_7d: Boolean! = false, $favs_last_30d: Boolean! = false, $favs_all_time: Boolean! = true) {\n  insert_queries_one(object: $object, on_conflict: $on_conflict) {\n    ...Query\n    favorite_queries(where: {user_id: {_eq: $session_id}}, limit: 1) {\n      created_at\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment Query on queries {\n  ...BaseQuery\n  ...QueryVisualizations\n  ...QueryForked\n  ...QueryUsers\n  ...QueryFavorites\n  __typename\n}\n\nfragment BaseQuery on queries {\n  id\n  dataset_id\n  name\n  description\n  query\n  private_to_group_id\n  is_temp\n  is_archived\n  created_at\n  updated_at\n  schedule\n  tags\n  parameters\n  __typename\n}\n\nfragment QueryVisualizations on queries {\n  visualizations {\n    id\n    type\n    name\n    options\n    created_at\n    __typename\n  }\n  __typename\n}\n\nfragment QueryForked on queries {\n  forked_query {\n    id\n    name\n    user {\n      name\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n\nfragment QueryUsers on queries {\n  user {\n    ...User\n    __typename\n  }\n  __typename\n}\n\nfragment User on users {\n  id\n  name\n  profile_image_url\n  __typename\n}\n\nfragment QueryFavorites on queries {\n  query_favorite_count_all @include(if: $favs_all_time) {\n    favorite_count\n    __typename\n  }\n  query_favorite_count_last_24h @include(if: $favs_last_24h) {\n    favorite_count\n    __typename\n  }\n  query_favorite_count_last_7d @include(if: $favs_last_7d) {\n    favorite_count\n    __typename\n  }\n  query_favorite_count_last_30d @include(if: $favs_last_30d) {\n    favorite_count\n    __typename\n  }\n  __typename\n}\n",
    }
