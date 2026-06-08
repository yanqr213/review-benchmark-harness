import unittest

from review_benchmark_harness.checks import evaluate_thresholds


class ChecksTests(unittest.TestCase):
    def test_evaluate_thresholds_ok(self):
        issues = evaluate_thresholds({"precision": 1.0, "recall": 1.0, "f1": 1.0, "rule_coverage": 1.0, "fp": 0, "fn": 0})
        self.assertEqual([], issues)

    def test_evaluate_thresholds_collects_failures(self):
        issues = evaluate_thresholds(
            {"precision": 0.3, "recall": 0.4, "f1": 0.35, "rule_coverage": 0.2, "fp": 4, "fn": 5},
            min_precision=0.8,
            min_recall=0.8,
            min_f1=0.8,
            min_rule_coverage=0.8,
            max_fp=1,
            max_fn=1,
            check_level="warning",
        )
        self.assertEqual(6, len(issues))
        self.assertEqual("warning", issues[0]["severity"])
