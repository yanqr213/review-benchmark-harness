from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .matching import match_findings
from .models import CaseScore, ReviewCase, ScoreReport


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    if denominator == 0:
        return default
    return numerator / denominator


def round_metric(value: float) -> float:
    return round(value, 4)


def score_case(case: ReviewCase, predicted_findings: List[Any]) -> CaseScore:
    bundle = match_findings(case.expected_findings, predicted_findings)
    tp = len(bundle.matched)
    fp = len(bundle.unmatched_predicted)
    fn = len(bundle.unmatched_expected)
    if case.expected_findings or predicted_findings:
        precision = safe_divide(tp, tp + fp)
        recall = safe_divide(tp, tp + fn)
        f1 = safe_divide(2 * precision * recall, precision + recall)
    else:
        precision = recall = f1 = 1.0
    severity_hits = sum(1 for item in bundle.matched if item.severity_match)
    file_hits = sum(1 for item in bundle.matched if item.file_score >= 0.8)
    line_distances = [item.line_distance for item in bundle.matched if item.line_distance is not None]
    expected_rules = {finding.rule_id for finding in case.expected_findings}
    matched_rules = {
        case.expected_findings[item.expected_index].rule_id
        for item in bundle.matched
        if item.expected_index < len(case.expected_findings)
    }
    return CaseScore(
        case_id=case.case_id,
        title=case.title,
        expected_count=len(case.expected_findings),
        predicted_count=len(predicted_findings),
        tp=tp,
        fp=fp,
        fn=fn,
        precision=round_metric(precision),
        recall=round_metric(recall),
        f1=round_metric(f1),
        severity_accuracy=round_metric(safe_divide(severity_hits, tp, default=1.0 if tp == 0 else 0.0)),
        rule_coverage=round_metric(safe_divide(len(matched_rules), len(expected_rules), default=1.0 if not expected_rules else 0.0)),
        file_match_rate=round_metric(safe_divide(file_hits, tp, default=1.0 if tp == 0 else 0.0)),
        average_line_distance=round_metric(safe_divide(sum(line_distances), len(line_distances), default=0.0)),
        matched=bundle.matched,
        unmatched_expected=bundle.unmatched_expected,
        unmatched_predicted=bundle.unmatched_predicted,
    )


def aggregate_scores(
    suite_name: str,
    system_name: str,
    case_scores: List[CaseScore],
    config: Optional[Dict[str, Any]] = None,
) -> ScoreReport:
    total_tp = sum(case.tp for case in case_scores)
    total_fp = sum(case.fp for case in case_scores)
    total_fn = sum(case.fn for case in case_scores)
    precision = safe_divide(total_tp, total_tp + total_fp)
    recall = safe_divide(total_tp, total_tp + total_fn)
    f1 = safe_divide(2 * precision * recall, precision + recall)
    matched_cases = [case for case in case_scores if case.tp > 0]
    metrics = {
        "cases": len(case_scores),
        "tp": total_tp,
        "fp": total_fp,
        "fn": total_fn,
        "precision": round_metric(precision),
        "recall": round_metric(recall),
        "f1": round_metric(f1),
        "rule_coverage": round_metric(safe_divide(sum(case.rule_coverage for case in case_scores), len(case_scores), default=0.0)),
        "severity_accuracy": round_metric(
            safe_divide(sum(case.severity_accuracy for case in matched_cases), len(matched_cases), default=1.0)
        ),
        "file_match_rate": round_metric(
            safe_divide(sum(case.file_match_rate for case in matched_cases), len(matched_cases), default=1.0)
        ),
        "average_line_distance": round_metric(
            safe_divide(sum(case.average_line_distance for case in matched_cases), len(matched_cases), default=0.0)
        ),
        "perfect_cases": sum(1 for case in case_scores if case.fp == 0 and case.fn == 0),
    }
    return ScoreReport(
        suite_name=suite_name,
        system_name=system_name,
        generated_at=datetime.now(timezone.utc).isoformat(),
        metrics=metrics,
        cases=case_scores,
        config=config or {},
    )
