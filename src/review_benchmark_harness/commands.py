from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .checks import evaluate_thresholds
from .io import load_json, load_suite, write_json, write_text
from .metrics import aggregate_scores, score_case
from .normalization import findings_to_dicts, normalize_file
from .reports import (
    compare_delta,
    comparison_rows,
    render_case_csv,
    render_compare_csv,
    render_compare_markdown,
    render_junit,
    render_markdown,
    score_report_json,
)


def resolve_prediction_file(predictions_root: Path, case_id: str) -> Optional[Path]:
    if predictions_root.is_file():
        return predictions_root
    for extension in (".json", ".md", ".markdown", ".txt"):
        candidate = predictions_root / f"{case_id}{extension}"
        if candidate.exists():
            return candidate
    return None


def score_suite(
    suite_dir: str,
    predictions_path: str,
    system_name: str = "candidate",
    input_format: str = "auto",
    min_precision: float | None = None,
    min_recall: float | None = None,
    min_f1: float | None = None,
    min_rule_coverage: float | None = None,
    max_fp: int | None = None,
    max_fn: int | None = None,
    check_level: str = "error",
) -> Dict[str, Any]:
    suite = load_suite(suite_dir)
    predictions_root = Path(predictions_path)
    case_scores = []
    for case in suite["cases"]:
        prediction_file = resolve_prediction_file(predictions_root, case.case_id)
        findings = normalize_file(str(prediction_file), input_format) if prediction_file else []
        case_scores.append(score_case(case, findings))
    report = aggregate_scores(
        suite_name=suite["suite_name"],
        system_name=system_name,
        case_scores=case_scores,
        config={
            "suite_dir": suite_dir,
            "predictions_path": predictions_path,
            "input_format": input_format,
        },
    )
    report.issues = evaluate_thresholds(
        report.metrics,
        min_precision=min_precision,
        min_recall=min_recall,
        min_f1=min_f1,
        min_rule_coverage=min_rule_coverage,
        max_fp=max_fp,
        max_fn=max_fn,
        check_level=check_level,
    )
    return score_report_json(report)


def write_score_outputs(
    report_payload: Dict[str, Any],
    json_output: str | None = None,
    markdown_output: str | None = None,
    csv_output: str | None = None,
    junit_output: str | None = None,
) -> None:
    report_obj = _report_from_payload(report_payload)
    if json_output:
        write_json(json_output, report_payload)
    if markdown_output:
        write_text(markdown_output, render_markdown(report_obj))
    if csv_output:
        write_text(csv_output, render_case_csv(report_obj))
    if junit_output:
        write_text(junit_output, render_junit(report_obj))


def _report_from_payload(payload: Dict[str, Any]):
    from .models import CaseScore, MatchDetail, ScoreReport

    cases = []
    for case in payload["cases"]:
        cases.append(
            CaseScore(
                case_id=case["case_id"],
                title=case["title"],
                expected_count=case["expected_count"],
                predicted_count=case["predicted_count"],
                tp=case["tp"],
                fp=case["fp"],
                fn=case["fn"],
                precision=case["precision"],
                recall=case["recall"],
                f1=case["f1"],
                severity_accuracy=case["severity_accuracy"],
                rule_coverage=case["rule_coverage"],
                file_match_rate=case["file_match_rate"],
                average_line_distance=case["average_line_distance"],
                matched=[MatchDetail(**item) for item in case.get("matched", [])],
                unmatched_expected=[],
                unmatched_predicted=[],
            )
        )
    return ScoreReport(
        suite_name=payload["suite_name"],
        system_name=payload["system_name"],
        generated_at=payload["generated_at"],
        metrics=payload["metrics"],
        config=payload.get("config", {}),
        issues=payload.get("issues", []),
        cases=cases,
    )


def normalize_output_command(input_path: str, output_path: str, input_format: str = "auto") -> Dict[str, Any]:
    findings = normalize_file(input_path, input_format=input_format)
    payload = {"findings": findings_to_dicts(findings)}
    write_json(output_path, payload)
    return payload


def compare_reports(report_paths: Iterable[str]) -> Dict[str, Any]:
    reports = [load_json(path) for path in report_paths]
    rows = comparison_rows(reports)
    deltas = [compare_delta(reports[0], reports[1])] if len(reports) >= 2 else []
    return {"rows": rows, "deltas": deltas}


def write_compare_outputs(
    compare_payload: Dict[str, Any],
    json_output: str | None = None,
    markdown_output: str | None = None,
    csv_output: str | None = None,
) -> None:
    if json_output:
        write_json(json_output, compare_payload)
    if markdown_output:
        write_text(markdown_output, render_compare_markdown(compare_payload["rows"], compare_payload["deltas"]))
    if csv_output:
        write_text(csv_output, render_compare_csv(compare_payload["rows"]))


def check_report(
    report_path: str,
    min_precision: float | None = None,
    min_recall: float | None = None,
    min_f1: float | None = None,
    min_rule_coverage: float | None = None,
    max_fp: int | None = None,
    max_fn: int | None = None,
    check_level: str = "error",
) -> Dict[str, Any]:
    report = load_json(report_path)
    metrics = report.get("metrics", report)
    issues = evaluate_thresholds(
        metrics,
        min_precision=min_precision,
        min_recall=min_recall,
        min_f1=min_f1,
        min_rule_coverage=min_rule_coverage,
        max_fp=max_fp,
        max_fn=max_fn,
        check_level=check_level,
    )
    return {"ok": not issues, "issues": issues, "metrics": metrics}


def init_suite(target_dir: str, with_sample: bool = True, force: bool = False) -> Dict[str, Any]:
    root = Path(target_dir)
    for relative in ("cases", "patches", "predictions", "reports"):
        (root / relative).mkdir(parents=True, exist_ok=True)
    manifest_path = root / "manifest.json"
    if manifest_path.exists() and not force:
        raise FileExistsError(f"{manifest_path} already exists; use --force to overwrite sample files.")
    manifest = {
        "name": root.name,
        "version": 1,
        "cases": ["SAMPLE-001"],
    }
    write_json(str(manifest_path), manifest)
    case_payload = {
        "case_id": "SAMPLE-001",
        "title": "Template finding for a swallowed exception",
        "patch": "patches/SAMPLE-001.diff",
        "expected_findings": [
            {
                "file": "src/service.py",
                "line": 12,
                "severity": "warning",
                "rule_id": "python.swallowed-exception",
                "title": "Broad exception hides failure state",
                "message": "The new code catches Exception and only logs it.",
            }
        ],
        "metadata": {"language": "python"},
    }
    write_json(str(root / "cases" / "SAMPLE-001.json"), case_payload)
    patch_text = """diff --git a/src/service.py b/src/service.py
--- a/src/service.py
+++ b/src/service.py
@@ -9,3 +9,7 @@ def run_job():
     try:
         perform()
-    except ValueError:
-        raise
+    except Exception:
+        logger.info("ignored")
+        return False
"""
    write_text(str(root / "patches" / "SAMPLE-001.diff"), patch_text)
    if with_sample:
        sample_review = """# Review

- [warning] src/service.py line 12: broad exception hides failure state (rule: python.swallowed-exception)
"""
        write_text(str(root / "predictions" / "SAMPLE-001.md"), sample_review)
    return {"suite": str(root), "manifest": manifest}
