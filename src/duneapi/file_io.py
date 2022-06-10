"""Utility code for I/O related tasks"""
import csv
import os
from dataclasses import fields, astuple, dataclass, is_dataclass
from typing import Any

FILE_OUT_PATH = os.environ.get("FILE_OUT_PATH", "./out")


@dataclass
class File:
    """Simple structure for declaring and passing around filenames"""

    name: str
    path: str = FILE_OUT_PATH

    def filename(self) -> str:
        """Returns the complete path to file"""
        return os.path.join(self.path, self.name)

    def __str__(self) -> str:
        return self.filename()


def write_to_csv(data_list: list[Any], outfile: File) -> None:
    """Writes `data_list` to `filename` as csv"""
    print(f"dumping {len(data_list)} results to {outfile.name}")

    # Creates out path if it doesn't exist.
    if not os.path.exists(outfile.path):
        os.makedirs(outfile.path)

    with open(outfile.filename(), "w", encoding="utf-8") as out_file:
        if len(data_list) == 0:
            return
        sample = data_list[0]
        assert is_dataclass(sample), "Method only accepts lists of type dataclass"
        headers = [f.name for f in fields(sample)]
        data_tuple = [astuple(x) for x in data_list]

        dict_writer = csv.DictWriter(out_file, headers, lineterminator="\n")
        dict_writer.writeheader()
        writer = csv.writer(out_file, lineterminator="\n")
        writer.writerows(data_tuple)
