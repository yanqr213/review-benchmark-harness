import unittest

from review_benchmark_harness.diff_parser import parse_unified_diff, strip_diff_prefix, touched_lines_by_file


SAMPLE_DIFF = """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -2,3 +2,4 @@ def run():
     start()
-    old()
+    new()
     end()
diff --git a/web/view.ts b/web/view.ts
--- a/web/view.ts
+++ b/web/view.ts
@@ -10,1 +10,2 @@ export function view() {
-  return oldValue;
+  const x = 1;
+  return x;
"""


class DiffParserTests(unittest.TestCase):
    def test_parse_returns_multiple_files(self):
        parsed = parse_unified_diff(SAMPLE_DIFF)
        self.assertEqual(2, len(parsed))

    def test_strip_diff_prefix(self):
        self.assertEqual("src/app.py", strip_diff_prefix("a/src/app.py"))

    def test_display_path_uses_new_path(self):
        parsed = parse_unified_diff(SAMPLE_DIFF)
        self.assertEqual("src/app.py", parsed[0].display_path)

    def test_added_lines_recorded(self):
        parsed = parse_unified_diff(SAMPLE_DIFF)
        self.assertEqual([3], parsed[0].hunks[0].added_lines)

    def test_removed_lines_recorded(self):
        parsed = parse_unified_diff(SAMPLE_DIFF)
        self.assertEqual([3], parsed[0].hunks[0].removed_lines)

    def test_touched_lines_by_file(self):
        touched = touched_lines_by_file(SAMPLE_DIFF)
        self.assertIn(3, touched["src/app.py"])
        self.assertIn(10, touched["web/view.ts"])
