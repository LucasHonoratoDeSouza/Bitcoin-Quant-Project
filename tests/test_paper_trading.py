import tempfile
import unittest
from pathlib import Path

from src.execution.accounting import AccountingSystem
from src.main_paper_trading import upsert_score_history


class TestPaperTradingHelpers(unittest.TestCase):
    def test_score_history_is_upserted_by_date(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = Path(tmp_dir) / "score_history.csv"

            upsert_score_history("2025-12-01", 10.0, 20.0, csv_path=csv_path)
            upsert_score_history("2025-12-01", 30.0, 40.0, csv_path=csv_path)

            lines = csv_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(lines[0], "Date,Long_Term_Score,Medium_Term_Score")
            self.assertEqual(lines[1], "2025-12-01,30.00,40.00")

    def test_update_daily_replaces_snapshot_for_same_date(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            state_path = Path(tmp_dir) / "portfolio_state.json"
            accounting = AccountingSystem(state_file=state_path)

            accounting.initialize(current_price=100.0)
            accounting.update_daily(current_price=100.0, date_str="2025-12-01")
            accounting.update_daily(current_price=110.0, date_str="2025-12-01")

            state = accounting.get_state()
            self.assertEqual(len(state["history"]), 1)
            self.assertEqual(state["history"][0]["date"], "2025-12-01")
            self.assertEqual(state["history"][0]["price"], 110.0)


if __name__ == "__main__":
    unittest.main()
