import unittest
from datetime import datetime

from duneapi.util import datetime_parser, open_query, duplicates, DUNE_DATE_FORMAT


class TestUtilities(unittest.TestCase):
    def test_date_parser(self):
        # def datetime_parser(dct: dict[str, Any]) -> dict[str, Any]:
        no_dates = {"a": 1, "b": "hello", "c": [None, 3.14]}
        self.assertEqual(datetime_parser(no_dates), no_dates)

        valid_date_str = "1985-03-10 05:00:00"
        invalid_date_str = "1985/03/10 - literally anything else"
        with_date = {"valid_date": valid_date_str, "invalid_date": invalid_date_str}
        self.assertEqual(
            datetime_parser(with_date),
            {
                "valid_date": datetime.strptime(valid_date_str, DUNE_DATE_FORMAT),
                "invalid_date": invalid_date_str,
            },
        )

    def test_open_query(self):
        query = "select 10 - '{{IntParameter}}' as value"
        self.assertEqual(query, open_query("./tests/queries/test_query.sql"))

    def test_duplicates(self):
        self.assertEqual(duplicates([1, 2]), [])
        self.assertEqual(duplicates([1, 2, 2, 4]), [2])
        self.assertEqual(duplicates([1, 1, 2, 2]), [1, 2])

        with self.assertRaises(TypeError) as err:
            duplicates([{"x": 1, "y": 2}])


if __name__ == "__main__":
    unittest.main()
