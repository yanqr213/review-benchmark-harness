import json
import tempfile
import unittest
from pathlib import Path

from review_benchmark_harness.cli import main


class CliTests(unittest.TestCase):
    def test_score_command_stdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "score.json"
            exit_code = main(
                [
                    "score",
                    "--suite",
                    "examples/sample-suite",
                    "--predictions",
                    "examples/sample-suite/predictions/good",
                    "--output",
                    str(output),
                ]
            )
            self.assertEqual(0, exit_code)
            self.assertTrue(output.exists())

    def test_init_suite_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            exit_code = main(["init-suite", str(Path(tmp) / "suite")])
            self.assertEqual(0, exit_code)

    def test_normalize_output_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "review.md"
            target = Path(tmp) / "norm" / "report.json"
            source.write_text("- [warning] src/a.py line 1: issue", encoding="utf-8")
            exit_code = main(["normalize-output", str(source), "--output", str(target)])
            self.assertEqual(0, exit_code)
            payload = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(1, len(payload["findings"]))

    def test_compare_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "a.json"
            second = Path(tmp) / "b.json"
            first.write_text(
                json.dumps(
                    {
                        "suite_name": "suite",
                        "system_name": "a",
                        "metrics": {
                            "precision": 1.0,
                            "recall": 1.0,
                            "f1": 1.0,
                            "rule_coverage": 1.0,
                            "severity_accuracy": 1.0,
                        },
                    }
                ),
                encoding="utf-8",
            )
            second.write_text(
                json.dumps(
                    {
                        "suite_name": "suite",
                        "system_name": "b",
                        "metrics": {
                            "precision": 0.5,
                            "recall": 0.5,
                            "f1": 0.5,
                            "rule_coverage": 0.5,
                            "severity_accuracy": 0.5,
                        },
                    }
                ),
                encoding="utf-8",
            )
            output = Path(tmp) / "cmp" / "leaderboard.json"
            exit_code = main(["compare", str(first), str(second), "--output", str(output)])
            self.assertEqual(0, exit_code)
            self.assertTrue(output.exists())

    def test_check_command_returns_error_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "score.json"
            report.write_text(
                json.dumps(
                    {
                        "metrics": {
                            "precision": 0.2,
                            "recall": 0.2,
                            "f1": 0.2,
                            "rule_coverage": 0.2,
                            "fp": 10,
                            "fn": 10,
                        }
                    }
                ),
                encoding="utf-8",
            )
            exit_code = main(["check", str(report), "--min-f1", "0.9", "--check", "error"])
            self.assertEqual(1, exit_code)
