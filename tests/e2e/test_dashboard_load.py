import unittest

from src.duneapi.api import DuneAPI
from src.duneapi.dashboard import DuneDashboard


class TestDashboard(unittest.TestCase):
    def test_load(self):
        configured_dashboard = DuneDashboard.from_file(
            api=DuneAPI.new_from_environment(),
            filename="./example/dashboard/_config.json",
        )
        configured_dashboard.update()

        fetched_dashboard = DuneDashboard.from_dune(
            api=DuneAPI.new_from_environment(),
            dashboard_slug="Demo-Dashboard",
            save_config=False,
        )
        self.assertEqual(fetched_dashboard, configured_dashboard)


if __name__ == "__main__":
    unittest.main()
