import unittest
from datetime import date
from pathlib import Path

from src.utils.project_paths import dated_json_path, normalize_date


class TestProjectPaths(unittest.TestCase):
    def test_normalize_date_accepts_iso_string(self):
        self.assertEqual(normalize_date("2025-12-19"), date(2025, 12, 19))

    def test_dated_json_path_builds_expected_filename(self):
        path = dated_json_path(Path("data/raw"), "daily_data", "2025-12-19")
        self.assertEqual(str(path), "data/raw/daily_data_2025-12-19.json")


if __name__ == "__main__":
    unittest.main()
