from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .models import Finding, ReviewCase, ScoreReport


def ensure_parent(path: Path) -> None:
    parent = path.parent
    if parent and not parent.exists():
        parent.mkdir(parents=True, exist_ok=True)


def write_text(path: str, content: str) -> None:
    target = Path(path)
    ensure_parent(target)
    with target.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(content)


def write_json(path: str, payload: Any) -> None:
    target = Path(path)
    ensure_parent(target)
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def finding_to_dict(finding: Finding) -> Dict[str, Any]:
    return {
        "file": finding.file,
        "line": finding.line,
        "severity": finding.severity,
        "rule_id": finding.rule_id,
        "title": finding.title,
        "message": finding.message,
    }


def case_to_dict(case: ReviewCase) -> Dict[str, Any]:
    return {
        "case_id": case.case_id,
        "title": case.title,
        "patch_path": case.patch_path,
        "expected_findings": [finding_to_dict(item) for item in case.expected_findings],
        "metadata": case.metadata,
    }


def score_report_to_dict(report: ScoreReport) -> Dict[str, Any]:
    return {
        "suite_name": report.suite_name,
        "system_name": report.system_name,
        "generated_at": report.generated_at,
        "metrics": report.metrics,
        "config": report.config,
        "issues": report.issues,
        "cases": [
            {
                "case_id": case.case_id,
                "title": case.title,
                "expected_count": case.expected_count,
                "predicted_count": case.predicted_count,
                "tp": case.tp,
                "fp": case.fp,
                "fn": case.fn,
                "precision": case.precision,
                "recall": case.recall,
                "f1": case.f1,
                "severity_accuracy": case.severity_accuracy,
                "rule_coverage": case.rule_coverage,
                "file_match_rate": case.file_match_rate,
                "average_line_distance": case.average_line_distance,
                "matched": [asdict(match) for match in case.matched],
                "unmatched_expected": [finding_to_dict(item) for item in case.unmatched_expected],
                "unmatched_predicted": [finding_to_dict(item) for item in case.unmatched_predicted],
            }
            for case in report.cases
        ],
    }


def load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_suite(suite_dir: str) -> Dict[str, Any]:
    root = Path(suite_dir)
    manifest_path = root / "manifest.json"
    manifest = load_json(str(manifest_path))
    cases: List[ReviewCase] = []
    for case_entry in manifest.get("cases", []):
        if isinstance(case_entry, str):
            case_path = root / "cases" / f"{case_entry}.json"
        else:
            case_path = root / "cases" / case_entry["file"]
        payload = load_json(str(case_path))
        patch_path = root / payload["patch"]
        expected = [Finding(**item, raw=item) for item in payload.get("expected_findings", [])]
        cases.append(
            ReviewCase(
                case_id=payload["case_id"],
                title=payload["title"],
                patch_path=str(patch_path),
                patch_text=patch_path.read_text(encoding="utf-8"),
                expected_findings=expected,
                metadata=payload.get("metadata", {}),
            )
        )
    return {"suite_name": manifest.get("name", root.name), "root": str(root), "cases": cases}
