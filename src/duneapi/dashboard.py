"""Dashboard management class"""
from __future__ import annotations

import argparse
import json
import os
from typing import Any

from .api import DuneAPI
from .constants import FIND_DASHBOARD_POST, FIND_QUERY_POST
from .logger import set_log
from .types import DuneQuery, DashboardTile, Post, Network, QueryParameter
from .util import duplicates

BASE_URL = "https://dune.xyz"
log = set_log(__name__)


class DuplicateQueryError(Exception):
    """Basic extension of Exception class"""


class DuneDashboard:
    """
    A Dune Dashboard consists of a family of queries
    Primary functionality is to update all of them
    without having to manually click refresh.
    """

    name: str
    url: str
    queries: list[DuneQuery]
    api: DuneAPI

    def __init__(
        self, api: DuneAPI, name: str, slug: str, user: str, queries: list[DuneQuery]
    ):
        dupes = duplicates([(q.raw_sql, q.network) for q in queries])
        if dupes:
            log.warning(f"Duplicate Query Detected {dupes}")
            # raise DuplicateQueryError(dupes)

        if api.username != user:
            raise ValueError(
                f"Attempt to load dashboard queries for invalid user {user} != {api.username}."
            )
        self.name = name
        self.slug = slug
        self.url = "/".join([BASE_URL, user, slug])
        self.queries = list(queries)
        self.api = api

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DuneDashboard):
            return NotImplemented
        equality_conditions = [
            self.name == other.name,
            self.slug == other.slug,
            self.url == other.url,
            self.queries == other.queries,
        ]
        log.debug(f"Equality conditions: {equality_conditions}")
        return all(equality_conditions)

    @classmethod
    def from_file(cls, api: DuneAPI, filename: str) -> DuneDashboard:
        """Constructs Dashboard from configuration file"""
        with open(filename, "r", encoding="utf-8") as config:
            return cls.from_json(api=api, json_obj=json.loads(config.read()))

    @classmethod
    def from_dune(
        cls, api: DuneAPI, dashboard_slug: str, save_config: bool = True
    ) -> DuneDashboard:
        """
        Initialized instance by fetching existing Dashboard from Dune.
        When save_config is True, Saves dashboard config files in ./out
        """
        post_data = {
            "operationName": "FindDashboard",
            "variables": {
                "session_id": 0,
                "user": api.username,
                "slug": dashboard_slug,
            },
            "query": FIND_DASHBOARD_POST,
        }
        response = api.post_dune_request(
            Post(data=post_data, key_map={"dashboards": {"visualization_widgets"}})
        )
        meta = response.json()["data"]["dashboards"][0]
        widgets = meta["visualization_widgets"]
        queries = set()
        for widget in widgets:
            query_data = widget["visualization"]
            query_id = query_data["query_details"]["query_id"]

            post = Post(
                data={
                    "operationName": "FindQuery",
                    "variables": {"session_id": 87, "id": query_id},
                    "query": FIND_QUERY_POST,
                },
                key_map={},
            )
            response = api.post_dune_request(post)
            query_data = response.json()["data"]["queries"][0]
            # Filtering out queries that are not owned by logged-in user.
            if query_data["user"]["name"] == api.username:
                queries.add(
                    DuneQuery(
                        name=query_data["name"],
                        description=query_data["description"],
                        raw_sql=query_data["query"],
                        network=Network(query_data["dataset_id"]),
                        parameters=[
                            QueryParameter.from_dict(p)
                            for p in query_data["parameters"]
                        ],
                        query_id=query_data["id"],
                    )
                )
            else:
                log.info(
                    f'Ignoring dashboard query from user {query_data["user"]["name"]}'
                )

        dashboard_owner = meta["user"]["name"]
        assert dashboard_owner == api.username, "Dashboard not owned by user"

        if save_config:
            cls.dump_config(
                name=meta["name"],
                owner=dashboard_owner,
                slug=dashboard_slug,
                queries=list(queries),
            )
        return cls(
            api=api,
            name=meta["name"],
            slug=dashboard_slug,
            queries=list(queries),
            user=dashboard_owner,
        )

    @staticmethod
    def dump_config(name: str, owner: str, slug: str, queries: list[DuneQuery]) -> None:
        """
        Writes Dashboard Configuration to files.
        Specifically to ./out/Dashboard-Slug
        """
        out_dir = f"./out/{slug}"
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
        queries_seen = {}
        with open(f"{out_dir}/_config.json", "w", encoding="utf-8") as config_file:
            query_dicts = []
            for query in queries:
                query_file = f"{query.name.lower().replace(' ', '-')}.sql"
                query_config = {
                    "id": query.query_id,
                    "name": query.name,
                    "description": query.description,
                    "query_file": query_file,
                    "network": str(query.network),
                    "parameters": [
                        {"key": p.key, "value": p.value, "type": p.type.value}
                        for p in query.parameters
                    ],
                }
                query_dicts.append(query_config)

                if query.raw_sql not in queries_seen:
                    # Whenever we encounter a new SQL query, write to file
                    query_path = f"{out_dir}/{query_file}"
                    with open(query_path, "w", encoding="utf-8") as q_file:
                        q_file.write(query.raw_sql.strip("\n") + "\n")
                    queries_seen[query.raw_sql] = query_file
                else:
                    # If already seen use the already existing file.
                    query_config["query_file"] = queries_seen[query.raw_sql]

            config_dict = {
                "meta": {
                    # Dashboards can be renamed but the slug doesn't change.
                    "name": name,
                    "slug": slug,
                    "user": owner,
                    "query_path": out_dir,
                },
                "queries": query_dicts,
            }
            config_file.write(
                json.dumps(config_dict, indent=2, default=str).strip("\n") + "\n"
            )

    @classmethod
    def from_json(cls, api: DuneAPI, json_obj: dict[str, Any]) -> DuneDashboard:
        """Constructs Dashboard from json file"""
        meta, queries = json_obj["meta"], json_obj["queries"]
        # TODO - tiles could be phased out of this program.
        tiles = [DashboardTile.from_dict(q, meta["query_path"]) for q in queries]
        queries = [DuneQuery.from_tile(tile) for tile in tiles]
        name = meta["name"]
        return cls(
            api=api,
            name=name,
            # Dashboards can be renamed, but slug is permanent.
            # So we chose slug with priority and use name otherwise.
            slug=meta.get("slug", name.replace(" ", "-")),
            user=meta["user"],
            queries=queries,
        )

    def update(self) -> None:
        """Creates a dune connection and updates/refreshes all dashboard queries"""
        for tile in self.queries:
            self.api.initiate_query(tile)
            self.api.execute_query(tile)

    def __str__(self) -> str:
        names = "\n".join(
            f"  {q.name}: {BASE_URL}/queries/{q.query_id}" for q in self.queries
        )
        return f'Dashboard "{self.name}": {self.url}\nQueries:\n{names}'


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch Allocation Receipts for a list of accounts"
    )
    parser.add_argument(
        "--dashboard-slug",
        type=str,
        help="The hyphenated last part of the dashboard URL",
    )
    args = parser.parse_args()

    dune = DuneAPI.new_from_environment()
    dashboard = DuneDashboard.from_dune(dune, args.dashboard_slug)
    print("Updated", dashboard)
