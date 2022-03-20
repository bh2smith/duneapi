"""
A simple framework for interacting with not officially supported DuneAnalytics API
Code adapted from https://github.com/itzmestar/duneanalytics
at commit bdccd5ba543a8f3679e2c81e18cee846af47bc52
"""
from __future__ import annotations

import logging.config
import os
import time
from typing import Optional

from requests import Session, Response

from src.request import (
    get_result_post,
    find_result_post,
    execute_query_post,
    initiate_query_post,
    Post,
)
from src.response import (
    validate_and_parse_dict_response,
    validate_and_parse_list_response,
)
from src.types import (
    Network,
    QueryParameter,
    DuneRecord,
    QueryResults,
    DuneSQLQuery,
)

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

    def initiate_query(self, query: DuneSQLQuery) -> None:
        """
        Initiates a new query.
        If no exception is raised, post was success!
        """
        post_data = initiate_query_post(query)
        response = self.post_dune_request(post_data)
        validate_and_parse_dict_response(response, post_data.key_map)

    def execute_query(self) -> None:
        """Executes query at query_id"""
        post_data = execute_query_post(self.query_id)
        response = self.post_dune_request(post_data)
        validate_and_parse_dict_response(response, post_data.key_map)

    def query_result_id(self) -> Optional[str]:
        """
        Fetch the query result id for a query
        :return: string representation of integer result id
        """
        post_data = get_result_post(self.query_id)
        response = self.post_dune_request(post_data)
        response_data = validate_and_parse_dict_response(response, post_data.key_map)

        return response_data["get_result"].get("result_id", None)

    def get_results(self) -> list[DuneRecord]:
        """Fetch the result for a query by id"""
        result_id = self.query_result_id()
        while not result_id:
            time.sleep(self.ping_frequency)
            log.debug("Awaiting results... ")
            result_id = self.query_result_id()
        post_data = find_result_post(result_id)
        response = self.post_dune_request(post_data)
        response_data = validate_and_parse_list_response(response, post_data.key_map)
        return QueryResults(response_data).data

    def post_dune_request(self, post: Post) -> Response:
        """
        Refresh Authorization Token and posts query.
        Parses response for errors by key and raises runtime error if they exist.
        Only successful responses are returned
        :param post: JSON content and validation parameters for request
        :return: response in json format
        """
        self.refresh_auth_token()
        response = self.session.post(GRAPH_URL, json=post.data)

        return response

    def execute_and_await_results(self) -> list[DuneRecord]:
        """
        Executes query by ID and awaits completion.
        :return: parsed list of dict records returned from query
        """
        self.execute_query()
        data_set = self.get_results()
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
        self.initiate_query(
            DuneSQLQuery(
                query_id=self.query_id,
                raw_sql=query_str,
                network=network,
                name="Auto Generated Query",
                parameters=parameters or [],
            )
        )
        for _ in range(0, self.max_retries):
            try:
                return self.execute_and_await_results()
            except RuntimeError as err:
                log.warning(
                    f"failed with {err}. Re-establishing connection and trying again"
                )
                self.login()
                self.refresh_auth_token()
        raise Exception(f"Maximum retries ({self.max_retries}) exceeded")
