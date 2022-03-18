"""Sample Fetch script from DuneAnalytics"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

from src.dune_analytics import DuneAnalytics, Network, QueryParameter


@dataclass
class Record:
    """Total amount reimbursed for accounting period"""

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


def fetch_records(dune: DuneAnalytics) -> list[Record]:
    """Initiates and executes Dune query, returning results as Python Objects"""
    results = dune.fetch(
        query_str=dune.open_query("./src/sample_query.sql"),
        name="Sample Query",
        network=Network.MAINNET,
        parameters=[
            QueryParameter.number_type("IntParam", 10),
            QueryParameter.date_type(
                "DateParam", datetime.strptime("2022-03-10", "%Y-%m-%d")
            ),
            QueryParameter.text_type("TextParam", "aba"),
        ],
    )
    return [Record.from_dict(row) for row in results]


if __name__ == "__main__":
    records = fetch_records(DuneAnalytics.new_from_environment())
    print("First result:", records[0])
