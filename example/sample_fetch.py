"""Sample Fetch script from DuneAnalytics"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.duneapi.api import DuneAPI
from src.duneapi.query import DuneQuery
from src.duneapi.types import Network, QueryParameter
from src.duneapi.util import open_query


@dataclass
class Record:
    """Arbitrary record with a few different data types"""

    string: str
    integer: int
    decimal: float
    time: datetime

    @classmethod
    def from_dict(cls, obj: dict[str, str]) -> Record:
        """Constructs Record from Dune Data as string dict"""
        return cls(
            string=obj["block_hash"],
            integer=int(obj["number"]),
            decimal=float(obj["tx_fees"]),
            # Dune timestamps are UTC!
            time=datetime.strptime(obj["time"], "%Y-%m-%dT%H:%M:%S+00:00"),
        )


def fetch_records(dune: DuneAPI) -> list[Record]:
    """Initiates and executes Dune query, returning results as Python Objects"""
    sample_query = DuneQuery.from_environment(
        raw_sql=open_query("./example/sample_query.sql"),
        name="Sample Query",
        network=Network.MAINNET,
        parameters=[
            QueryParameter.number_type("IntParam", 10),
            QueryParameter.date_type("DateParam", datetime(2022, 3, 10, 12, 30, 30)),
            QueryParameter.text_type("TextParam", "aba"),
        ],
    )
    results = dune.fetch(sample_query)
    return [Record.from_dict(row) for row in results]


if __name__ == "__main__":
    records = fetch_records(DuneAPI.new_from_environment())
    print("First result:", records[0])
