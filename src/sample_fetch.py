"""Sample Fetch script from DuneAnalytics"""
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
    return [
        Record(
            string=row["block_hash"],
            integer=row["number"],
            decimal=row["tx_fees"],
            time=row["time"],
        )
        for row in results
    ]


if __name__ == "__main__":
    records = fetch_records(DuneAnalytics.new_from_environment())
    print("First result:", records[0])
