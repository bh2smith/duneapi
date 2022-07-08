import unittest

from duneapi.api import DuneAPI
from duneapi.dashboard import DuneDashboard


class TestDashboard(unittest.TestCase):
    def test_update(self):
        dashboard = DuneDashboard.from_file(
            api=DuneAPI.new_from_environment(),
            filename="./example/dashboard/_config.json",
        )
        dashboard.update()
        query2 = dashboard.queries[1]
        self.assertEqual(dashboard.api.fetch(query2), [{"val": "1337"}])

        # Modify the query (by changing the parameter) and update dashboard
        query2.parameters[0].value = 10
        dashboard.update()
        self.assertEqual(dashboard.api.fetch(query2), [{"val": "10"}])


if __name__ == "__main__":
    unittest.main()
