from __future__ import annotations

from pathlib import Path
import json
import re
from typing import Any, Dict, Iterable, List, Optional

from .models import Finding


SEVERITY_ALIASES = {
    "blocker": "error",
    "critical": "error",
    "error": "error",
    "high": "error",
    "major": "warning",
    "warning": "warning",
    "warn": "warning",
    "medium": "warning",
    "minor": "info",
    "low": "info",
    "info": "info",
    "note": "info",
}

PATH_RE = re.compile(r"(?P<path>[\w./\\-]+\.[A-Za-z0-9_+-]+)")
LINE_RE = re.compile(r"(?:line|Line|L)(?:\s*|:)(?P<line>\d+)")
SEVERITY_RE = re.compile(
    r"\b(blocker|critical|error|high|major|warning|warn|medium|minor|low|info|note)\b",
    re.IGNORECASE,
)
RULE_RE = re.compile(r"(?:rule|check|code)\s*[:#]\s*([A-Za-z0-9_.-]+)", re.IGNORECASE)
BACKTICK_RULE_RE = re.compile(r"`([A-Za-z0-9_.-]{3,})`")


def normalize_severity(value: Any) -> str:
    if value is None:
        return "warning"
    text = str(value).strip().lower()
    return SEVERITY_ALIASES.get(text, "warning")


def coerce_finding(data: Dict[str, Any]) -> Finding:
    file_value = (
        data.get("file")
        or data.get("path")
        or data.get("filename")
        or data.get("location", {}).get("file")
        or "unknown"
    )
    line_value = (
        data.get("line")
        or data.get("start_line")
        or data.get("location", {}).get("line")
        or data.get("location", {}).get("start_line")
    )
    try:
        line = int(line_value) if line_value is not None else None
    except (TypeError, ValueError):
        line = None
    rule_id = (
        data.get("rule_id")
        or data.get("rule")
        or data.get("check")
        or data.get("code")
        or "unspecified"
    )
    title = data.get("title") or data.get("summary") or data.get("message") or "Untitled finding"
    message = (
        data.get("message")
        or data.get("description")
        or data.get("body")
        or data.get("text")
        or title
    )
    return Finding(
        file=str(file_value).replace("\\", "/"),
        line=line,
        severity=normalize_severity(data.get("severity") or data.get("level") or data.get("priority")),
        rule_id=str(rule_id),
        title=str(title),
        message=str(message),
        raw=data,
    )


def extract_findings_from_json(data: Any) -> List[Finding]:
    if isinstance(data, list):
        return [coerce_finding(item) for item in data if isinstance(item, dict)]
    if not isinstance(data, dict):
        return []
    for key in ("findings", "issues", "reviews", "results", "comments"):
        value = data.get(key)
        if isinstance(value, list):
            return [coerce_finding(item) for item in value if isinstance(item, dict)]
    if any(key in data for key in ("file", "path", "message", "title")):
        return [coerce_finding(data)]
    return []


def parse_markdown_findings(text: str) -> List[Finding]:
    findings: List[Finding] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if not re.match(r"^([-*+]|\d+\.)\s+", line):
            continue
        body = re.sub(r"^([-*+]|\d+\.)\s+", "", line)
        file_match = PATH_RE.search(body)
        line_match = LINE_RE.search(body)
        severity_match = SEVERITY_RE.search(body)
        rule_match = RULE_RE.search(body) or BACKTICK_RULE_RE.search(body)
        title = body
        message = body
        findings.append(
            Finding(
                file=file_match.group("path").replace("\\", "/") if file_match else "unknown",
                line=int(line_match.group("line")) if line_match else None,
                severity=normalize_severity(severity_match.group(1)) if severity_match else "warning",
                rule_id=rule_match.group(1) if rule_match else "unspecified",
                title=title,
                message=message,
                raw={"source": "markdown", "line": raw_line},
            )
        )
    return findings


def detect_format(text: str, hint: str = "auto") -> str:
    if hint != "auto":
        return hint
    stripped = text.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        return "json"
    return "markdown"


def normalize_text(text: str, input_format: str = "auto") -> List[Finding]:
    fmt = detect_format(text, input_format)
    if fmt == "json":
        data = json.loads(text)
        return extract_findings_from_json(data)
    return parse_markdown_findings(text)


def normalize_file(path: str, input_format: str = "auto") -> List[Finding]:
    content = Path(path).read_text(encoding="utf-8")
    return normalize_text(content, input_format=input_format)


def findings_to_dicts(findings: Iterable[Finding]) -> List[Dict[str, Any]]:
    return [
        {
            "file": finding.file,
            "line": finding.line,
            "severity": finding.severity,
            "rule_id": finding.rule_id,
            "title": finding.title,
            "message": finding.message,
        }
        for finding in findings
    ]
