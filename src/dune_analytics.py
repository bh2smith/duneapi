"""
A simple framework for interacting with not officially supported DuneAnalytics API
Code adapted from https://github.com/itzmestar/duneanalytics
at commit bdccd5ba543a8f3679e2c81e18cee846af47bc52
"""
from __future__ import annotations

import logging.config
import os
import time
from datetime import datetime
from enum import Enum
from typing import Optional, Any, Collection

from requests import Session

log = logging.getLogger(__name__)
logging.config.fileConfig(fname="logging.conf", disable_existing_loggers=True)

BASE_URL = "https://dune.xyz"
GRAPH_URL = "https://core-hsr.dune.xyz/v1/graphql"

RawDuneResponse = dict[str, dict[str, list[dict[str, dict[str, str]]]]]

ParsedDuneResponse = list[dict[str, str]]


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

    def login_and_fetch_auth(self) -> None:
        """combines both of `login` and `fetch_auth_token`"""
        self.login()
        self.fetch_auth_token()

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
        self.handle_dune_request(query_data)

    def execute_query(self):  # type: ignore
        """Executes query at query_id"""
        query_data = {
            "operationName": "ExecuteQuery",
            "variables": {"query_id": self.query_id, "parameters": []},
            "query": "mutation ExecuteQuery($query_id: Int!, $parameters: [Parameter!]!)"
            "{\n  execute_query(query_id: $query_id, parameters: $parameters) "
            "{\n    job_id\n    __typename\n  }\n}\n",
        }
        return self.handle_dune_request(query_data)

    def query_result_id(self) -> Optional[str]:
        """
        Fetch the query result id for a query
        :return: string representation of integer result id
        """
        query_data = {
            "operationName": "GetResult",
            "variables": {"query_id": self.query_id},
            "query": "query GetResult($query_id: Int!, $parameters: [Parameter!]) "
            "{\n  get_result(query_id: $query_id, parameters: $parameters) "
            "{\n    job_id\n    result_id\n    __typename\n  }\n}\n",
        }

        data = self.handle_dune_request(query_data)
        result_id = data.get("data").get("get_result").get("result_id")
        return str(result_id) if result_id else None

    def query_result(self, result_id: str):  # type: ignore
        """Fetch the result for a query by id"""
        query_data = {
            "operationName": "FindResultDataByResult",
            "variables": {"result_id": result_id},
            "query": "query FindResultDataByResult($result_id: uuid!) "
            "{\n  query_results(where: {id: {_eq: $result_id}}) "
            "{\n    id\n    job_id\n    error\n    runtime\n    "
            "generated_at\n    columns\n    __typename\n  }"
            "\n  get_result_by_result_id(args: {want_result_id: $result_id}) "
            "{\n    data\n    __typename\n  }\n}\n",
        }

        return self.handle_dune_request(query_data)

    def handle_dune_request(self, query: dict[str, Collection[str]]):  # type: ignore
        """
        Parses response for errors by key and raises runtime error if they exist.
        Successful responses will be printed to std-out and response json returned
        :param query: JSON content for request POST
        :return: response in json format
        """
        self.session.headers.update({"authorization": f"Bearer {self.token}"})
        response = self.session.post(GRAPH_URL, json=query)
        response_json = response.json()
        if "errors" in response_json:
            raise RuntimeError("Dune API Request failed with", response_json)
        return response_json

    def execute_and_await_results(self, sleep_time: int) -> ParsedDuneResponse:
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
        data = self.query_result(result_id)
        data_set = self.parse_response(data)
        log.info(f"got {len(data_set)} records from last query")
        return data_set

    def fetch(
        self,
        query_str: str,
        network: Network,
        name: str,
        parameters: Optional[list[QueryParameter]] = None,
    ) -> ParsedDuneResponse:
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
            except RuntimeError as err:
                log.warning(
                    f"fetch failed with {err}. Re-establishing connection and trying again"
                )
                self.login_and_fetch_auth()
        raise Exception(f"Maximum retries ({self.max_retries}) exceeded")

    @staticmethod
    def open_query(filepath: str) -> str:
        """Opens `filename` and returns as string"""
        with open(filepath, "r", encoding="utf-8") as query_file:
            return query_file.read()

    @staticmethod
    def parse_response(data: RawDuneResponse) -> ParsedDuneResponse:
        """Parses user data and execution date from query result."""
        return [rec["data"] for rec in data["data"]["get_result_by_result_id"]]
