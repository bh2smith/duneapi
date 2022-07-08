from duneapi.api import DuneAPI
from duneapi.dashboard import DuneDashboard


if __name__ == "__main__":
    DuneDashboard.from_dune(
        api=DuneAPI.new_from_environment(), dashboard_slug="Demo-Dashboard"
    )
