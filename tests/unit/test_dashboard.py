import unittest


class MyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.valid_input = """{
          "meta": {
            "name": "Test-Dashboard",
            "url": "bh2smith/Demo-Dashboard"
          },
          "queries": [
            {
              "id": 533353,
              "name": "Example 1",
              "query_file": "./example/dashboard/query1.sql",
              "network": "mainnet",
              "requires": "./example/dashboard/base_query.sql"
            },
            {
              "id": 533351,
              "name": "Example 2",
              "query_file": "./example/dashboard/query2.sql",
              "network": "gchain"
            }
          ]
        }"""

    def test_something(self):
        self.assertEqual(True, False)  # add assertion here


if __name__ == "__main__":
    unittest.main()
