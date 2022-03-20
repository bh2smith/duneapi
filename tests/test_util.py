import unittest
from datetime import datetime

from src.util import datetime_parser


class TestUtilities(unittest.TestCase):
    def test_date_parser(self):
        # def datetime_parser(dct: dict[str, Any]) -> dict[str, Any]:
        no_dates = {"a": 1, "b": "hello", "c": [None, 3.14]}
        self.assertEqual(datetime_parser(no_dates), no_dates)

        valid_date_str = "1985-03-10T05:00:00+00:00"
        invalid_date_str = "1985/03/10 - literally anything else"
        with_date = {"valid_date": valid_date_str, "invalid_date": invalid_date_str}
        self.assertEqual(
            datetime_parser(with_date),
            {
                "valid_date": datetime.strptime(
                    valid_date_str, "%Y-%m-%dT%H:%M:%S+00:00"
                ),
                "invalid_date": invalid_date_str,
            },
        )


if __name__ == "__main__":
    unittest.main()
