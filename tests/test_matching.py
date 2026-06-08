import unittest

from review_benchmark_harness.matching import (
    file_similarity,
    finding_match_score,
    line_similarity,
    match_findings,
    normalize_path,
    severity_similarity,
)
from review_benchmark_harness.models import Finding


class MatchingTests(unittest.TestCase):
    def setUp(self):
        self.expected = Finding(
            file="src/service.py",
            line=12,
            severity="warning",
            rule_id="python.swallowed-exception",
            title="Broad exception hides failure state",
            message="The code catches Exception.",
        )
        self.predicted = Finding(
            file="service.py",
            line=13,
            severity="warning",
            rule_id="python.swallowed-exception",
            title="Broad exception hides failure state",
            message="The patch catches Exception and returns.",
        )

    def test_normalize_path(self):
        self.assertEqual("src/service.py", normalize_path("./src\\service.py"))

    def test_file_similarity_exact(self):
        self.assertEqual(1.0, file_similarity("src/a.py", "src/a.py"))

    def test_file_similarity_suffix(self):
        self.assertGreaterEqual(file_similarity("src/service.py", "service.py"), 0.9)

    def test_line_similarity_with_tolerance(self):
        self.assertGreater(line_similarity(12, 14), 0.0)

    def test_severity_similarity_adjacent(self):
        self.assertEqual(0.5, severity_similarity("warning", "error"))

    def test_finding_match_score_positive(self):
        self.assertGreater(finding_match_score(self.expected, self.predicted), 0.7)

    def test_match_findings_one_match(self):
        bundle = match_findings([self.expected], [self.predicted])
        self.assertEqual(1, len(bundle.matched))

    def test_match_findings_unmatched_prediction(self):
        unrelated = Finding(
            file="web/ui.ts",
            line=1,
            severity="info",
            rule_id="style.rule",
            title="style",
            message="style",
        )
        bundle = match_findings([self.expected], [unrelated])
        self.assertEqual(1, len(bundle.unmatched_predicted))
