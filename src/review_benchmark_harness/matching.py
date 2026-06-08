from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import List, Optional

from .models import Finding, MatchDetail


def normalize_path(path: str) -> str:
    return path.replace("\\", "/").lstrip("./").lower()


def suffix_match_score(expected: str, predicted: str) -> float:
    expected_parts = normalize_path(expected).split("/")
    predicted_parts = normalize_path(predicted).split("/")
    common = 0
    for left, right in zip(reversed(expected_parts), reversed(predicted_parts)):
        if left != right:
            break
        common += 1
    return common / max(len(expected_parts), len(predicted_parts), 1)


def file_similarity(expected: str, predicted: str) -> float:
    left = normalize_path(expected)
    right = normalize_path(predicted)
    if left == right:
        return 1.0
    if left.endswith(right) or right.endswith(left):
        return 0.92
    suffix_score = suffix_match_score(left, right)
    if suffix_score >= 0.5:
        return 0.65 + (suffix_score * 0.3)
    left_base = left.rsplit("/", 1)[-1]
    right_base = right.rsplit("/", 1)[-1]
    if left_base == right_base:
        return 0.7
    return SequenceMatcher(None, left, right).ratio() * 0.6


def text_similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    if left == right:
        return 1.0
    return SequenceMatcher(None, left.lower(), right.lower()).ratio()


def severity_similarity(expected: str, predicted: str) -> float:
    if expected == predicted:
        return 1.0
    order = {"info": 0, "warning": 1, "error": 2}
    if expected not in order or predicted not in order:
        return 0.0
    distance = abs(order[expected] - order[predicted])
    return 0.5 if distance == 1 else 0.0


def line_similarity(expected: Optional[int], predicted: Optional[int], tolerance: int = 5) -> float:
    if expected is None or predicted is None:
        return 0.55
    distance = abs(expected - predicted)
    if distance == 0:
        return 1.0
    if distance > tolerance:
        return 0.0
    return max(0.0, 1 - (distance / (tolerance + 1)))


def finding_match_score(expected: Finding, predicted: Finding) -> float:
    file_score = file_similarity(expected.file, predicted.file)
    line_score = line_similarity(expected.line, predicted.line)
    rule_score = text_similarity(expected.rule_id, predicted.rule_id)
    message_score = max(
        text_similarity(expected.title, predicted.title),
        text_similarity(expected.message, predicted.message),
    )
    severity_score = severity_similarity(expected.severity, predicted.severity)
    return (
        (file_score * 0.32)
        + (line_score * 0.2)
        + (rule_score * 0.22)
        + (message_score * 0.16)
        + (severity_score * 0.1)
    )


@dataclass
class MatchBundle:
    matched: List[MatchDetail]
    unmatched_expected: List[Finding]
    unmatched_predicted: List[Finding]


def match_findings(expected: List[Finding], predicted: List[Finding], threshold: float = 0.55) -> MatchBundle:
    pairs = []
    for expected_index, expected_finding in enumerate(expected):
        for predicted_index, predicted_finding in enumerate(predicted):
            score = finding_match_score(expected_finding, predicted_finding)
            if score < threshold:
                continue
            file_score = file_similarity(expected_finding.file, predicted_finding.file)
            line_distance = None
            if expected_finding.line is not None and predicted_finding.line is not None:
                line_distance = abs(expected_finding.line - predicted_finding.line)
            pairs.append(
                (
                    score,
                    MatchDetail(
                        expected_index=expected_index,
                        predicted_index=predicted_index,
                        score=round(score, 4),
                        file_score=round(file_score, 4),
                        line_distance=line_distance,
                        severity_match=expected_finding.severity == predicted_finding.severity,
                        rule_match=expected_finding.rule_id == predicted_finding.rule_id,
                    ),
                )
            )
    pairs.sort(key=lambda item: item[0], reverse=True)
    matched: List[MatchDetail] = []
    used_expected = set()
    used_predicted = set()
    for _, detail in pairs:
        if detail.expected_index in used_expected or detail.predicted_index in used_predicted:
            continue
        used_expected.add(detail.expected_index)
        used_predicted.add(detail.predicted_index)
        matched.append(detail)
    unmatched_expected = [item for index, item in enumerate(expected) if index not in used_expected]
    unmatched_predicted = [item for index, item in enumerate(predicted) if index not in used_predicted]
    return MatchBundle(
        matched=matched,
        unmatched_expected=unmatched_expected,
        unmatched_predicted=unmatched_predicted,
    )
