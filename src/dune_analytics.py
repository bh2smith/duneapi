"""
A simple framework for interacting with not officially supported DuneAnalytics API
Code adapted from https://github.com/itzmestar/duneanalytics
at commit bdccd5ba543a8f3679e2c81e18cee846af47bc52
"""
from __future__ import annotations

import logging.config
import os
import time
from typing import Optional, Collection

from requests import Session, Response

from src.dune_types import Network, QueryParameter, DuneRecord, QueryResults
from src.operations import get_result_post, find_result_post, execute_query_post

log = logging.getLogger(__name__)
logging.config.fileConfig(fname="logging.conf", disable_existing_loggers=True)

BASE_URL = "https://dune.xyz"
GRAPH_URL = "https://core-hsr.dune.xyz/v1/graphql"


class DuneAnalytics:
    """
    Acts as API client for dune.xyz. All requests to be made through this class.
    """

    def __init__(
        self,
        username: str,
        password: str,
        query_id: int,
        max_retries: int = 2,
        ping_frequency: int = 5,
    ):
        """
        Initialize the object
        :param username: username for dune.xyz
        :param password: password for dune.xyz
        :param query_id: existing integer query id owned `username`
        """
        self.csrf = None
        self.auth_refresh = None
        self.token = None
        self.username = username
        self.password = password
        self.query_id = int(query_id)
        self.session = Session()
        self.max_retries = max_retries
        self.ping_frequency = ping_frequency
        headers = {
            "origin": BASE_URL,
            "sec-ch-ua": "empty",
            "sec-ch-ua-mobile": "?0",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "dnt": "1",
        }
        self.session.headers.update(headers)

    @staticmethod
    def new_from_environment() -> DuneAnalytics:
        """Initialize & authenticate a Dune client from the current environment"""
        dune = DuneAnalytics(
            os.environ["DUNE_USER"],
            os.environ["DUNE_PASSWORD"],
            int(os.environ["DUNE_QUERY_ID"]),
        )
        dune.login()
        dune.fetch_auth_token()
        return dune

    def login(self) -> None:
        """Attempt to log in to dune.xyz & get the token"""
        login_url = BASE_URL + "/auth/login"
        csrf_url = BASE_URL + "/api/auth/csrf"
        auth_url = BASE_URL + "/api/auth"

        # fetch login page
        self.session.get(login_url)

        # get csrf token
        self.session.post(csrf_url)
        self.csrf = self.session.cookies.get("csrf")

        # try to log in
        form_data = {
            "action": "login",
            "username": self.username,
            "password": self.password,
            "csrf": self.csrf,
            "next": BASE_URL,
        }

        self.session.post(auth_url, data=form_data)
        self.auth_refresh = self.session.cookies.get("auth-refresh")

    def fetch_auth_token(self) -> None:
        """Fetch authorization token for the user"""
        session_url = BASE_URL + "/api/auth/session"

        response = self.session.post(session_url)
        if response.status_code == 200:
            self.token = response.json().get("token")
        else:
            raise SystemExit(response)

    def refresh_auth_token(self) -> None:
        """Set authorization token for the user"""
        self.fetch_auth_token()
        self.session.headers.update({"authorization": f"Bearer {self.token}"})

    def initiate_new_query(
        self, query: str, name: str, network: Network, parameters: list[QueryParameter]
    ) -> None:
        """Initiates a new query"""
        query_data = {
            "operationName": "UpsertQuery",
            "variables": {
                "favs_last_24h": False,
                "favs_last_7d": False,
                "favs_last_30d": False,
                "favs_all_time": True,
                "object": {
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
                },
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
        # log.debug("Upsert Query") dict[str, dict[str, dict[str, Any]]]
        self.handle_dune_request(query_data)

    def execute_query(self) -> None:
        """Executes query at query_id"""
        query_data = execute_query_post(self.query_id)
        log.debug("Executing Query")
        self.post_dune_request(query_data)

    def query_result_id(self) -> Optional[str]:
        """
        Fetch the query result id for a query
        :return: string representation of integer result id
        """
        query_data = get_result_post(self.query_id)
        # log.debug("Fetching Result ID") dict[str, dict[str, dict[str, Optional[str]]
        data = self.handle_dune_request(query_data)
        result_id = data.get("data").get("get_result").get("result_id")
        return str(result_id) if result_id else None

    def query_result(self, result_id: str) -> list[DuneRecord]:
        """Fetch the result for a query by id"""
        query_data = find_result_post(result_id)
        response_json = self.post_dune_request(query_data).json()
        if "errors" in response_json:
            raise RuntimeError("Request Error. Failed with", response_json)

        return QueryResults(response_json).data

    def post_dune_request(self, query: dict[str, Collection[str]]) -> Response:
        """Refresh Authorization Token and post query"""
        self.refresh_auth_token()
        response = self.session.post(GRAPH_URL, json=query)
        if response.status_code != 200:
            raise SystemExit("Dune post failed with", response)
        return response

    def handle_dune_request(self, query: dict[str, Collection[str]]):  # type: ignore
        """
        Parses response for errors by key and raises runtime error if they exist.
        Successful responses will be printed to std-out and response json returned
        :param query: JSON content for request POST
        :return: response in json format
        """
        self.refresh_auth_token()
        response = self.session.post(GRAPH_URL, json=query)
        response_json = response.json()
        if "errors" in response_json:
            raise RuntimeError("Dune API Request failed with", response_json)
        return response_json

    def execute_and_await_results(self, sleep_time: int) -> list[DuneRecord]:
        """
        Executes query by ID and awaits completion.
        Since queries take some time to complete we include a sleep parameter
        since there is no purpose in constantly pinging for results
        :param sleep_time: time to sleep between checking for results
        :return: parsed list of dict records returned from query
        """
        self.execute_query()
        result_id = self.query_result_id()
        while not result_id:
            time.sleep(sleep_time)
            result_id = self.query_result_id()
        data_set = self.query_result(result_id)
        log.info(f"got {len(data_set)} records from last query")
        return data_set

    def fetch(
        self,
        query_str: str,
        network: Network,
        name: str,
        parameters: Optional[list[QueryParameter]] = None,
    ) -> list[DuneRecord]:
        """
        Pushes new query and executes, awaiting query completion
        :param query_str: sql string to execute
        :param network: Network enum variant
        :param name: optional name of what is being fetched (for logging)
        :param parameters: optional parameters to be included in query
        :return: list of records as dictionaries
        """
        log.info(f"Fetching {name} on {network}...")
        self.initiate_new_query(
            query=query_str,
            network=network,
            name="Auto Generated Query",
            parameters=parameters or [],
        )
        for _ in range(0, self.max_retries):
            try:
                return self.execute_and_await_results(self.ping_frequency)
            except RuntimeError as e:
                log.warning(
                    f"failed with {e}.\nRe-establishing connection and trying again"
                )
                self.login()
                self.refresh_auth_token()
        raise Exception(f"Maximum retries ({self.max_retries}) exceeded")

    @staticmethod
    def open_query(filepath: str) -> str:
        """Opens `filename` and returns as string"""
        with open(filepath, "r", encoding="utf-8") as query_file:
            return query_file.read()
