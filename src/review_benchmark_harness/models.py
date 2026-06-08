from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Finding:
    file: str
    line: Optional[int]
    severity: str
    rule_id: str
    title: str
    message: str
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReviewCase:
    case_id: str
    title: str
    patch_path: str
    patch_text: str
    expected_findings: List[Finding]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MatchDetail:
    expected_index: int
    predicted_index: int
    score: float
    file_score: float
    line_distance: Optional[int]
    severity_match: bool
    rule_match: bool


@dataclass
class CaseScore:
    case_id: str
    title: str
    expected_count: int
    predicted_count: int
    tp: int
    fp: int
    fn: int
    precision: float
    recall: float
    f1: float
    severity_accuracy: float
    rule_coverage: float
    file_match_rate: float
    average_line_distance: float
    matched: List[MatchDetail] = field(default_factory=list)
    unmatched_expected: List[Finding] = field(default_factory=list)
    unmatched_predicted: List[Finding] = field(default_factory=list)


@dataclass
class ScoreReport:
    suite_name: str
    system_name: str
    generated_at: str
    metrics: Dict[str, Any]
    cases: List[CaseScore]
    config: Dict[str, Any]
    issues: List[Dict[str, Any]] = field(default_factory=list)
