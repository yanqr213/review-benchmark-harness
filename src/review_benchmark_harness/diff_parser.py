from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Dict, List, Optional, Set


HUNK_RE = re.compile(
    r"^@@ -(?P<old_start>\d+)(?:,(?P<old_count>\d+))? \+(?P<new_start>\d+)(?:,(?P<new_count>\d+))? @@"
)


@dataclass
class Hunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    added_lines: List[int] = field(default_factory=list)
    removed_lines: List[int] = field(default_factory=list)
    touched_new_lines: List[int] = field(default_factory=list)


@dataclass
class FileDiff:
    old_path: str
    new_path: str
    hunks: List[Hunk] = field(default_factory=list)

    @property
    def display_path(self) -> str:
        path = self.new_path if self.new_path != "/dev/null" else self.old_path
        return strip_diff_prefix(path)

    @property
    def touched_lines(self) -> Set[int]:
        result: Set[int] = set()
        for hunk in self.hunks:
            result.update(hunk.touched_new_lines)
        return result


def strip_diff_prefix(path: str) -> str:
    if path.startswith("a/") or path.startswith("b/"):
        return path[2:]
    return path


def parse_unified_diff(text: str) -> List[FileDiff]:
    files: List[FileDiff] = []
    current_file: Optional[FileDiff] = None
    current_hunk: Optional[Hunk] = None
    old_line = 0
    new_line = 0

    for raw_line in text.splitlines():
        if raw_line.startswith("diff --git "):
            parts = raw_line.split()
            old_path = parts[2] if len(parts) > 2 else ""
            new_path = parts[3] if len(parts) > 3 else ""
            current_file = FileDiff(old_path=old_path, new_path=new_path)
            files.append(current_file)
            current_hunk = None
            continue
        if raw_line.startswith("--- "):
            if current_file is None:
                current_file = FileDiff(old_path=raw_line[4:].strip(), new_path="")
                files.append(current_file)
            else:
                current_file.old_path = raw_line[4:].strip()
            continue
        if raw_line.startswith("+++ "):
            if current_file is None:
                current_file = FileDiff(old_path="", new_path=raw_line[4:].strip())
                files.append(current_file)
            else:
                current_file.new_path = raw_line[4:].strip()
            continue
        match = HUNK_RE.match(raw_line)
        if match:
            if current_file is None:
                current_file = FileDiff(old_path="", new_path="")
                files.append(current_file)
            current_hunk = Hunk(
                old_start=int(match.group("old_start")),
                old_count=int(match.group("old_count") or "1"),
                new_start=int(match.group("new_start")),
                new_count=int(match.group("new_count") or "1"),
            )
            current_file.hunks.append(current_hunk)
            old_line = current_hunk.old_start
            new_line = current_hunk.new_start
            continue
        if current_hunk is None:
            continue
        if not raw_line:
            prefix = " "
        else:
            prefix = raw_line[0]
        if prefix == " ":
            current_hunk.touched_new_lines.append(new_line)
            old_line += 1
            new_line += 1
        elif prefix == "+":
            current_hunk.added_lines.append(new_line)
            current_hunk.touched_new_lines.append(new_line)
            new_line += 1
        elif prefix == "-":
            current_hunk.removed_lines.append(old_line)
            current_hunk.touched_new_lines.append(max(new_line, 1))
            old_line += 1
    return files


def touched_lines_by_file(text: str) -> Dict[str, Set[int]]:
    touched: Dict[str, Set[int]] = {}
    for file_diff in parse_unified_diff(text):
        touched[file_diff.display_path] = file_diff.touched_lines
    return touched
