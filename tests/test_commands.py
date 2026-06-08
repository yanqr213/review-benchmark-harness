import json
import tempfile
import unittest
from pathlib import Path

from review_benchmark_harness.commands import (
    check_report,
    compare_reports,
    init_suite,
    normalize_output_command,
    score_suite,
    write_compare_outputs,
    write_score_outputs,
)


class CommandsTests(unittest.TestCase):
    def test_init_suite_creates_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload = init_suite(Path(tmp, "suite").as_posix())
            manifest = Path(payload["suite"]) / "manifest.json"
            self.assertTrue(manifest.exists())

    def test_normalize_output_command_writes_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "review.md"
            source.write_text("- [warning] src/a.py line 1: issue", encoding="utf-8")
            target = Path(tmp) / "out" / "normalized.json"
            payload = normalize_output_command(str(source), str(target))
            self.assertTrue(target.exists())
            self.assertEqual(1, len(payload["findings"]))

    def test_score_suite_on_example_good_predictions(self):
        payload = score_suite("examples/sample-suite", "examples/sample-suite/predictions/good", system_name="good")
        self.assertEqual("good", payload["system_name"])
        self.assertGreaterEqual(payload["metrics"]["f1"], 0.9)

    def test_write_score_outputs_creates_parent_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload = score_suite("examples/sample-suite", "examples/sample-suite/predictions/good")
            json_path = Path(tmp) / "nested" / "score.json"
            md_path = Path(tmp) / "nested" / "score.md"
            csv_path = Path(tmp) / "nested" / "score.csv"
            junit_path = Path(tmp) / "nested" / "junit.xml"
            write_score_outputs(payload, str(json_path), str(md_path), str(csv_path), str(junit_path))
            self.assertTrue(junit_path.exists())

    def test_compare_reports_returns_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.json"
            b = Path(tmp) / "b.json"
            a.write_text(json.dumps(score_suite("examples/sample-suite", "examples/sample-suite/predictions/good", system_name="a")), encoding="utf-8")
            b.write_text(json.dumps(score_suite("examples/sample-suite", "examples/sample-suite/predictions/noisy", system_name="b")), encoding="utf-8")
            payload = compare_reports([str(a), str(b)])
            self.assertEqual(2, len(payload["rows"]))

    def test_write_compare_outputs_creates_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp) / "a.json"
            b = Path(tmp) / "b.json"
            a.write_text(json.dumps(score_suite("examples/sample-suite", "examples/sample-suite/predictions/good", system_name="a")), encoding="utf-8")
            b.write_text(json.dumps(score_suite("examples/sample-suite", "examples/sample-suite/predictions/noisy", system_name="b")), encoding="utf-8")
            payload = compare_reports([str(a), str(b)])
            json_out = Path(tmp) / "reports" / "leaderboard.json"
            md_out = Path(tmp) / "reports" / "leaderboard.md"
            csv_out = Path(tmp) / "reports" / "leaderboard.csv"
            write_compare_outputs(payload, str(json_out), str(md_out), str(csv_out))
            self.assertTrue(md_out.exists())

    def test_check_report_fails_threshold(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "score.json"
            report.write_text(json.dumps(score_suite("examples/sample-suite", "examples/sample-suite/predictions/noisy")), encoding="utf-8")
            payload = check_report(str(report), min_f1=0.9, check_level="error")
            self.assertFalse(payload["ok"])
