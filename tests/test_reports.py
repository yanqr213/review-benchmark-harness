import unittest

from review_benchmark_harness.metrics import aggregate_scores, score_case
from review_benchmark_harness.models import Finding, ReviewCase
from review_benchmark_harness.reports import (
    compare_delta,
    comparison_rows,
    render_case_csv,
    render_compare_csv,
    render_compare_markdown,
    render_junit,
    render_markdown,
)


class ReportsTests(unittest.TestCase):
    def make_report(self):
        case = ReviewCase(
            case_id="RBH-1",
            title="Case",
            patch_path="patch.diff",
            patch_text="",
            expected_findings=[
                Finding(
                    file="src/a.py",
                    line=10,
                    severity="warning",
                    rule_id="python.rule",
                    title="Issue",
                    message="Issue",
                )
            ],
        )
        return aggregate_scores("suite", "bot", [score_case(case, list(case.expected_findings))])

    def test_render_markdown_contains_metrics(self):
        markdown = render_markdown(self.make_report())
        self.assertIn("| Precision | 1.0000 |", markdown)

    def test_render_case_csv_contains_header(self):
        csv_text = render_case_csv(self.make_report())
        self.assertIn("case_id,title,tp,fp,fn", csv_text)

    def test_render_junit_contains_testsuite(self):
        xml_text = render_junit(self.make_report())
        self.assertIn("<testsuite", xml_text)

    def test_comparison_rows_sorted_by_f1(self):
        rows = comparison_rows(
            [
                {"system_name": "b", "suite_name": "s", "metrics": {"precision": 0.9, "recall": 0.9, "f1": 0.9, "rule_coverage": 0.8, "severity_accuracy": 1.0}},
                {"system_name": "a", "suite_name": "s", "metrics": {"precision": 0.7, "recall": 0.7, "f1": 0.7, "rule_coverage": 0.8, "severity_accuracy": 1.0}},
            ]
        )
        self.assertEqual("b", rows[0]["system_name"])

    def test_render_compare_markdown_contains_leaderboard(self):
        rows = [{"system_name": "bot", "suite_name": "suite", "precision": 1.0, "recall": 1.0, "f1": 1.0, "rule_coverage": 1.0, "severity_accuracy": 1.0}]
        text = render_compare_markdown(rows)
        self.assertIn("# Leaderboard", text)

    def test_render_compare_csv_contains_system_name(self):
        rows = [{"system_name": "bot", "suite_name": "suite", "precision": 1.0, "recall": 1.0, "f1": 1.0, "rule_coverage": 1.0, "severity_accuracy": 1.0}]
        text = render_compare_csv(rows)
        self.assertIn("system_name", text)

    def test_compare_delta_returns_f1_delta(self):
        delta = compare_delta(
            {"system_name": "base", "metrics": {"precision": 0.5, "recall": 0.5, "f1": 0.5, "rule_coverage": 0.5}},
            {"system_name": "cand", "metrics": {"precision": 0.7, "recall": 0.6, "f1": 0.64, "rule_coverage": 0.8}},
        )
        self.assertEqual(0.14, delta["f1_delta"])
