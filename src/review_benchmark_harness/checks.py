from __future__ import annotations

from typing import Any, Dict, List


def evaluate_thresholds(
    metrics: Dict[str, Any],
    min_precision: float | None = None,
    min_recall: float | None = None,
    min_f1: float | None = None,
    min_rule_coverage: float | None = None,
    max_fp: int | None = None,
    max_fn: int | None = None,
    check_level: str = "error",
) -> List[Dict[str, Any]]:
    issues: List[Dict[str, Any]] = []

    def add_issue(message: str) -> None:
        issues.append({"severity": check_level, "message": message})

    if min_precision is not None and metrics.get("precision", 0.0) < min_precision:
        add_issue(f"precision {metrics.get('precision', 0.0):.4f} is below minimum {min_precision:.4f}")
    if min_recall is not None and metrics.get("recall", 0.0) < min_recall:
        add_issue(f"recall {metrics.get('recall', 0.0):.4f} is below minimum {min_recall:.4f}")
    if min_f1 is not None and metrics.get("f1", 0.0) < min_f1:
        add_issue(f"f1 {metrics.get('f1', 0.0):.4f} is below minimum {min_f1:.4f}")
    if min_rule_coverage is not None and metrics.get("rule_coverage", 0.0) < min_rule_coverage:
        add_issue(
            f"rule coverage {metrics.get('rule_coverage', 0.0):.4f} is below minimum {min_rule_coverage:.4f}"
        )
    if max_fp is not None and metrics.get("fp", 0) > max_fp:
        add_issue(f"fp {metrics.get('fp', 0)} exceeds maximum {max_fp}")
    if max_fn is not None and metrics.get("fn", 0) > max_fn:
        add_issue(f"fn {metrics.get('fn', 0)} exceeds maximum {max_fn}")
    return issues
