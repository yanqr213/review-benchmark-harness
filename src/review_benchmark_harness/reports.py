from __future__ import annotations

import csv
import io
from typing import Any, Dict, Iterable, List
from xml.etree.ElementTree import Element, SubElement, tostring

from .io import score_report_to_dict
from .models import ScoreReport


def render_markdown(report: ScoreReport) -> str:
    metrics = report.metrics
    lines = [
        f"# {report.suite_name} / {report.system_name}",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
        f"| Precision | {metrics['precision']:.4f} |",
        f"| Recall | {metrics['recall']:.4f} |",
        f"| F1 | {metrics['f1']:.4f} |",
        f"| Rule coverage | {metrics['rule_coverage']:.4f} |",
        f"| Severity accuracy | {metrics['severity_accuracy']:.4f} |",
        f"| File match rate | {metrics['file_match_rate']:.4f} |",
        f"| Avg line distance | {metrics['average_line_distance']:.4f} |",
        "",
        "## Cases",
        "",
        "| Case | TP | FP | FN | Precision | Recall | F1 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for case in report.cases:
        lines.append(
            f"| {case.case_id} | {case.tp} | {case.fp} | {case.fn} | {case.precision:.4f} | {case.recall:.4f} | {case.f1:.4f} |"
        )
    if report.issues:
        lines.extend(["", "## Checks", ""])
        for issue in report.issues:
            lines.append(f"- [{issue['severity']}] {issue['message']}")
    return "\n".join(lines) + "\n"


def render_case_csv(report: ScoreReport) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "case_id",
            "title",
            "tp",
            "fp",
            "fn",
            "precision",
            "recall",
            "f1",
            "rule_coverage",
            "severity_accuracy",
            "file_match_rate",
            "average_line_distance",
        ]
    )
    for case in report.cases:
        writer.writerow(
            [
                case.case_id,
                case.title,
                case.tp,
                case.fp,
                case.fn,
                case.precision,
                case.recall,
                case.f1,
                case.rule_coverage,
                case.severity_accuracy,
                case.file_match_rate,
                case.average_line_distance,
            ]
        )
    return buffer.getvalue()


def render_junit(report: ScoreReport) -> str:
    testsuite = Element(
        "testsuite",
        name=report.system_name,
        tests=str(len(report.cases)),
        failures=str(sum(1 for case in report.cases if case.fp or case.fn)),
    )
    for case in report.cases:
        testcase = SubElement(
            testsuite,
            "testcase",
            classname=report.suite_name,
            name=case.case_id,
        )
        if case.fp or case.fn:
            failure = SubElement(
                testcase,
                "failure",
                message=f"fp={case.fp}, fn={case.fn}, f1={case.f1:.4f}",
            )
            failure.text = f"Expected perfect match for {case.case_id}, got tp={case.tp}, fp={case.fp}, fn={case.fn}."
    return tostring(testsuite, encoding="unicode")


def comparison_rows(reports: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for report in reports:
        metrics = report["metrics"]
        rows.append(
            {
                "system_name": report["system_name"],
                "suite_name": report["suite_name"],
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1": metrics["f1"],
                "rule_coverage": metrics["rule_coverage"],
                "severity_accuracy": metrics["severity_accuracy"],
            }
        )
    rows.sort(key=lambda item: (-item["f1"], -item["recall"], -item["precision"], item["system_name"]))
    return rows


def render_compare_markdown(rows: List[Dict[str, Any]], deltas: List[Dict[str, Any]] | None = None) -> str:
    lines = [
        "# Leaderboard",
        "",
        "| Rank | System | Precision | Recall | F1 | Rule coverage | Severity accuracy |",
        "| ---: | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for index, row in enumerate(rows, start=1):
        lines.append(
            f"| {index} | {row['system_name']} | {row['precision']:.4f} | {row['recall']:.4f} | {row['f1']:.4f} | {row['rule_coverage']:.4f} | {row['severity_accuracy']:.4f} |"
        )
    if deltas:
        lines.extend(["", "## Delta", ""])
        for delta in deltas:
            lines.append(
                f"- {delta['candidate']} vs {delta['baseline']}: F1 {delta['f1_delta']:+.4f}, recall {delta['recall_delta']:+.4f}, precision {delta['precision_delta']:+.4f}"
            )
    return "\n".join(lines) + "\n"


def render_compare_csv(rows: List[Dict[str, Any]]) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "system_name",
            "suite_name",
            "precision",
            "recall",
            "f1",
            "rule_coverage",
            "severity_accuracy",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


def compare_delta(baseline: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "baseline": baseline["system_name"],
        "candidate": candidate["system_name"],
        "precision_delta": round(candidate["metrics"]["precision"] - baseline["metrics"]["precision"], 4),
        "recall_delta": round(candidate["metrics"]["recall"] - baseline["metrics"]["recall"], 4),
        "f1_delta": round(candidate["metrics"]["f1"] - baseline["metrics"]["f1"], 4),
        "rule_coverage_delta": round(candidate["metrics"]["rule_coverage"] - baseline["metrics"]["rule_coverage"], 4),
    }


def score_report_json(report: ScoreReport) -> Dict[str, Any]:
    return score_report_to_dict(report)
