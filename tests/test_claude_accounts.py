import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import usage  # noqa: E402


class ClaudeAccountsTests(unittest.TestCase):
    def test_reads_swap_accounts_in_sequence_with_active_flag(self):
        with tempfile.TemporaryDirectory() as d:
            os.mkdir(f"{d}/cache")
            json.dump({"activeAccountNumber": 3, "sequence": [2, 3]}, open(f"{d}/sequence.json", "w"))
            json.dump({"accounts": {
                "1": {"lastGood": {"five_hour": {"pct": 50}}},  # 순환 밖 → 빠짐
                "2": {"lastGood": {"five_hour": {"pct": 7.0, "resets_at": "2026-11-18T13:30:00+00:00"},
                                   "seven_day": {"pct": 1.0}}},
                "3": {},  # 아직 못 받음
            }}, open(f"{d}/cache/usage.json", "w"))
            with patch.object(usage, "SWAP_DIR", d):
                got = usage.claude_accounts()
        self.assertEqual([(n, on) for n, on, _, _ in got], [("CLAUDE2", False), ("CLAUDE3", True)])
        self.assertEqual(got[0][2].used_percent, 7.0)
        self.assertIsNotNone(got[0][2].resets_at)
        self.assertIsNone(got[1][3].used_percent)

    def test_no_swap_means_empty(self):
        with patch.object(usage, "SWAP_DIR", "/nonexistent"):
            self.assertEqual(usage.claude_accounts(), [])


if __name__ == "__main__":
    unittest.main()
