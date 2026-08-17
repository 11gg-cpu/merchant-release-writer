#!/usr/bin/env python3
"""Validate a merchant-facing release draft and optional image plan."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ALLOWED_TYPES = {"single", "standard", "campaign", "digest", "announcement"}
PLACEHOLDER_PATTERNS = (
    re.compile(r"<[^>\n]+>"),
    re.compile(r"\b(?:TODO|TBD|FIXME)\b", re.IGNORECASE),
)
INTERNAL_PATTERNS = (
    re.compile(r"(?:测试账号|内部域名|app[_ -]?secret|access[_ -]?token)", re.IGNORECASE),
)


def issue(level: str, code: str, message: str) -> dict[str, str]:
    return {"level": level, "code": code, "message": message}


def validate_draft(path: Path, content_type: str) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    issues: list[dict[str, str]] = []
    headings = re.findall(r"^#{1,6}\s+(.+)$", text, flags=re.MULTILINE)
    visible = re.sub(r"[`#>*_|\-]", "", text)
    visible_count = len(re.sub(r"\s+", "", visible))

    if not headings or not text.lstrip().startswith("# "):
        issues.append(issue("error", "missing_title", "Draft must start with one level-1 title."))
    if len(headings) < 3:
        issues.append(issue("error", "insufficient_structure", "Draft needs a title and at least two sections."))
    if visible_count < 180:
        issues.append(issue("warning", "draft_too_short", "Draft may not explain the scenario, steps, and limits."))
    if visible_count > 5000:
        issues.append(issue("warning", "draft_too_long", "Review mobile readability and remove internal detail."))
    if not re.search(r"(?:如何|步骤|使用|操作|时间线|商家动作)", text):
        issues.append(issue("warning", "missing_action", "No clear action or usage section was detected."))
    if not re.search(r"(?:注意|限制|范围|条件|适用|影响)", text):
        issues.append(issue("warning", "missing_limits", "No scope, condition, or limitation section was detected."))
    for pattern in PLACEHOLDER_PATTERNS:
        if pattern.search(text):
            issues.append(issue("error", "placeholder", f"Unresolved placeholder matched: {pattern.pattern}"))
    for pattern in INTERNAL_PATTERNS:
        if pattern.search(text):
            issues.append(issue("warning", "sensitive_term", f"Review possible internal detail: {pattern.pattern}"))
    if content_type == "announcement" and not re.search(r"(?:日期|时间|生效|截止)", text):
        issues.append(issue("error", "announcement_without_timeline", "Announcement needs an explicit timeline."))
    return issues


def validate_image_plan(path: Path) -> list[dict[str, str]]:
    issues: list[dict[str, str]] = []
    try:
        data: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [issue("error", "invalid_image_plan", str(exc))]

    if not isinstance(data, dict) or not isinstance(data.get("images"), list):
        return [issue("error", "invalid_image_plan", "Image plan must contain an images array.")]

    seen_ids: set[str] = set()
    for index, item in enumerate(data["images"], start=1):
        if not isinstance(item, dict):
            issues.append(issue("error", "invalid_image", f"Image {index} must be an object."))
            continue
        image_id = str(item.get("id", "")).strip()
        if not image_id:
            issues.append(issue("error", "missing_image_id", f"Image {index} has no id."))
        elif image_id in seen_ids:
            issues.append(issue("error", "duplicate_image_id", f"Duplicate image id: {image_id}"))
        seen_ids.add(image_id)
        if not str(item.get("purpose", "")).strip():
            issues.append(issue("error", "missing_image_purpose", f"Image {index} has no purpose."))
        source = str(item.get("source", "")).strip()
        if item.get("required") and not source:
            issues.append(issue("error", "missing_required_image", f"Required image {image_id or index} has no source."))
        if source and not re.match(r"https?://", source):
            source_path = Path(source).expanduser()
            if not source_path.is_file():
                issues.append(issue("error", "image_not_found", f"Image source not found: {source}"))
        if item.get("required") and item.get("redaction_checked") is not True:
            issues.append(issue("warning", "redaction_unchecked", f"Image {image_id or index} needs a redaction check."))
    return issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draft", type=Path, required=True)
    parser.add_argument("--type", required=True, choices=sorted(ALLOWED_TYPES))
    parser.add_argument("--image-plan", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.draft.is_file():
        print(json.dumps({"errors": [{"code": "draft_not_found", "message": str(args.draft)}]}))
        return 2

    issues = validate_draft(args.draft, args.type)
    if args.image_plan:
        issues.extend(validate_image_plan(args.image_plan))
    result = {
        "valid": not any(item["level"] == "error" for item in issues),
        "errors": [item for item in issues if item["level"] == "error"],
        "warnings": [item for item in issues if item["level"] == "warning"],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
