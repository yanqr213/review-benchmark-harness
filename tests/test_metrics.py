import unittest

from review_benchmark_harness.metrics import aggregate_scores, safe_divide, score_case
from review_benchmark_harness.models import Finding, ReviewCase


class MetricsTests(unittest.TestCase):
    def make_case(self):
        return ReviewCase(
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

    def test_safe_divide_default(self):
        self.assertEqual(0.0, safe_divide(1, 0))

    def test_score_case_perfect(self):
        case = self.make_case()
        score = score_case(case, list(case.expected_findings))
        self.assertEqual(1.0, score.f1)
        self.assertEqual(1.0, score.rule_coverage)

    def test_score_case_miss(self):
        case = self.make_case()
        score = score_case(case, [])
        self.assertEqual(0.0, score.recall)
        self.assertEqual(1, score.fn)

    def test_aggregate_scores(self):
        case = self.make_case()
        report = aggregate_scores("suite", "bot", [score_case(case, list(case.expected_findings))])
        self.assertEqual("suite", report.suite_name)
        self.assertEqual(1.0, report.metrics["f1"])
