# Dune Analytics API

[![Python 3.9](https://img.shields.io/badge/python-3.10-blue.svg)](https://www.python.org/downloads/release/python-3102/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Build](https://github.com/bh2smith/duneapi/actions/workflows/pull-request.yaml/badge.svg)](https://github.com/bh2smith/duneapi/actions/workflows/pull-request.yml)

A simple framework for interacting with Dune Analytics' unsupported API. The primary
class (`DuneAPI`) of this repo is adapted from
https://github.com/itzmestar/duneanalytics at commit
bdccd5ba543a8f3679e2c81e18cee846af47bc52

## Import as Project Dependency

```shell
pip install duneapi
```

Then you should be able to write python scripts similar to the following:

### Example Usage

Fill out your Dune credentials in the `.env` file. The Dune user and password are
straight-forward login credentials to Dune Analytics. The `DUNE_QUERY_ID` is an integer
id found in the URL of a query when saved in the Dune interface. This should be created
beforehand, but the same query id can be used everywhere throughout the program (as long
as it is owned by the account corresponding to the user credentials provided).

You do not have to provide the query id as an environment variable, but doing so, will
allow you to use the same id for all fetching needs. For dashboard management, you will
need to have a unique id for each query.

#### Execute Query and Fetch Results from Dune

```python
from duneapi.api import DuneAPI
from duneapi.query import DuneQuery
from duneapi.types import Network, QueryParameter, DuneRecord
from duneapi.util import open_query


def fetch_records(dune: DuneAPI) -> list[DuneRecord]:
    sample_query = DuneQuery.from_environment(
        raw_sql=open_query("PATH_TO_SOME_SQL_FILE"),
        name="Sample Query",
        network=Network.MAINNET,
        parameters=[
            QueryParameter.number_type("IntParam", 10),
            QueryParameter.text_type("TextParam", "aba"),
        ],
    )
    return dune.fetch(sample_query)


if __name__ == "__main__":
    dune_connection = DuneAPI.new_from_environment()
    records = fetch_records(dune_connection)
    print("First result:", records[0])
```

#### Dashboard Management

It will help to get aquainted with the Dashboard configuration file found in
[./example/dashboard/my_dashboard.json](./example/dashboard/my_dashboard.json). This
essentially requires filepath and query id to existing dune queries. Generally it is
expected that you will use the family of queries contained in an existing dashboard, but
there is no actual validation. Technically one could put all queries here and refresh
them with this tool.

```python
from duneapi.dashboard import DuneDashboard

dashboard = DuneDashboard("./example/dashboard/my_dashboard.json")
dashboard.update()
print("Updated", dashboard)
```

To fetch some sample ethereum block data, run the sample script as:

```shell
python -m example.sample_fetch
```

This will result in the following console logs:

```
got 10 records from last query
First record Record(
    string='0x255309e019abaf74bf2d58d4020547c89f875842abae1c874fb0d5ae8eac9859', 
    integer=14362177, 
    decimal=0.14785533, 
    time='2022-03-10T23:50:16+00:00'
)
```

To fetch your own data follow the code outline
in [sample_fetch.py](example/sample_fetch.py)

## Contributing and Local Development

Clone this Repo and install as follows.

```shell
python3 -m venv venv
source ./env/bin/activate
pip install -r requirements.txt
cp .env.sample .env       <----- Copy your Dune credentials here!
```

## Deployment

1. Bump the version number in [setup.py](setup.py)
2. Build the duneapi package `python -m build`
3. Upload to pypi `twine upload dist/* `