import json
import tempfile
import unittest
from pathlib import Path

from review_benchmark_harness.normalization import (
    detect_format,
    extract_findings_from_json,
    normalize_file,
    normalize_severity,
    normalize_text,
    parse_markdown_findings,
)


class NormalizationTests(unittest.TestCase):
    def test_normalize_severity_alias(self):
        self.assertEqual("error", normalize_severity("critical"))

    def test_detect_json_format(self):
        self.assertEqual("json", detect_format('{"findings": []}'))

    def test_detect_markdown_format(self):
        self.assertEqual("markdown", detect_format("- [warning] src/a.py line 3: issue"))

    def test_extract_findings_from_json_list(self):
        findings = extract_findings_from_json([{"file": "a.py", "line": 1, "message": "x"}])
        self.assertEqual(1, len(findings))
        self.assertEqual("a.py", findings[0].file)

    def test_parse_markdown_findings(self):
        text = "- [warning] src/service.py line 12: issue text (rule: python.rule)"
        findings = parse_markdown_findings(text)
        self.assertEqual("src/service.py", findings[0].file)
        self.assertEqual(12, findings[0].line)
        self.assertEqual("python.rule", findings[0].rule_id)

    def test_normalize_text_json(self):
        findings = normalize_text(json.dumps({"findings": [{"file": "a.py", "line": 2, "message": "x"}]}))
        self.assertEqual(1, len(findings))
        self.assertEqual(2, findings[0].line)

    def test_normalize_text_markdown(self):
        findings = normalize_text("- [error] web/auth.ts L44: issue (rule: web.open-redirect)")
        self.assertEqual("error", findings[0].severity)

    def test_normalize_file_reads_utf8(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "review.md"
            path.write_text("- [warning] src/a.py line 1: text", encoding="utf-8")
            findings = normalize_file(str(path))
            self.assertEqual(1, len(findings))
