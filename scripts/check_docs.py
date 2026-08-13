#!/usr/bin/env python3
"""Repository documentation and documented-contract checks (stdlib plus backend models)."""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {".git", ".venv", "node_modules"}
MARKDOWN_FILES = [
    path for path in ROOT.rglob("*.md") if not IGNORED_PARTS.intersection(path.parts)
]
FENCE_LANGUAGES = {
    "",
    "bash",
    "console",
    "csv",
    "http",
    "javascript",
    "json",
    "jsonc",
    "mermaid",
    "python",
    "sql",
    "text",
    "toml",
    "yaml",
}


def slug(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text).strip().lower()
    text = re.sub(r"[`*_~]", "", text)
    text = re.sub(r"[^\w\- ]", "", text, flags=re.UNICODE)
    return re.sub(r"[\s-]+", "-", text).strip("-")


def headings(path: Path) -> list[str]:
    return [
        slug(match.group(1))
        for line in path.read_text(encoding="utf-8").splitlines()
        if (match := re.match(r"^#{1,6}\s+(.+?)\s*#*\s*$", line))
    ]


def check_markdown() -> list[str]:
    errors: list[str] = []
    anchor_cache = {path.resolve(): headings(path) for path in MARKDOWN_FILES}
    link_pattern = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\s]+)(?:\s+[\"'][^\"']+[\"'])?\)")
    for path in MARKDOWN_FILES:
        lines = path.read_text(encoding="utf-8").splitlines()
        anchors = anchor_cache[path.resolve()]
        for anchor, count in Counter(anchors).items():
            if anchor and count > 1:
                errors.append(
                    f"{path.relative_to(ROOT)}: duplicate heading anchor #{anchor}"
                )

        fence: tuple[str, int] | None = None
        for number, line in enumerate(lines, 1):
            marker = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
            if marker:
                chars, info = marker.groups()
                if fence is None:
                    language = info.strip()
                    if " " in language or language not in FENCE_LANGUAGES:
                        errors.append(
                            f"{path.relative_to(ROOT)}:{number}: invalid fenced-code info string {language!r}"
                        )
                    fence = (chars[0], len(chars))
                elif chars[0] == fence[0] and len(chars) >= fence[1]:
                    if info.strip():
                        errors.append(
                            f"{path.relative_to(ROOT)}:{number}: closing fence has trailing text"
                        )
                    fence = None
        if fence:
            errors.append(f"{path.relative_to(ROOT)}: unclosed fenced-code block")

        text = "\n".join(lines)
        for raw_target in link_pattern.findall(text):
            target = unquote(raw_target.strip("<>"))
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith(("//", "mailto:")):
                continue
            file_part, fragment = parsed.path, parsed.fragment
            destination = (
                (path.parent / file_part).resolve() if file_part else path.resolve()
            )
            if not destination.exists():
                errors.append(
                    f"{path.relative_to(ROOT)}: broken relative link {raw_target}"
                )
            elif (
                fragment
                and destination.suffix.lower() == ".md"
                and slug(fragment)
                not in anchor_cache.get(destination, headings(destination))
            ):
                errors.append(
                    f"{path.relative_to(ROOT)}: missing anchor in {raw_target}"
                )
    return errors


def documented_api_routes() -> set[tuple[str, str]]:
    text = (ROOT / "backend/docs/api.md").read_text(encoding="utf-8")
    return set(
        re.findall(
            r"^\| `((?:GET|POST|PUT|PATCH|DELETE)) (/[^` ]+)` \|", text, re.MULTILINE
        )
    )


def check_api_routes() -> list[str]:
    sys.path.insert(0, str(ROOT / "backend"))
    from app.main import app

    schema = app.openapi()
    actual = {
        (method.upper(), path)
        for path, operations in schema["paths"].items()
        for method in operations
        if method.upper() in {"GET", "POST", "PUT", "PATCH", "DELETE"}
        and path.startswith(("/api/", "/health"))
    }
    documented = documented_api_routes()
    return contract_diff("backend endpoint inventory", actual, documented)


def check_frontend_routes() -> list[str]:
    source = (ROOT / "frontend/src/Routing.jsx").read_text(encoding="utf-8")
    actual = {
        value
        for value in re.findall(r"<Route\s+path=[\"']([^\"']+)", source)
        if value != "*"
    }
    matrix = (ROOT / "frontend/docs/architecture.md").read_text(encoding="utf-8")
    documented = set(re.findall(r"^\| `(/[^`]*)` \|", matrix, re.MULTILINE))
    return contract_diff("frontend route matrix", actual, documented)


def contract_diff(name: str, actual: set, documented: set) -> list[str]:
    errors = [
        f"{name}: undocumented registration {item}"
        for item in sorted(actual - documented)
    ]
    errors += [
        f"{name}: documented but not registered {item}"
        for item in sorted(documented - actual)
    ]
    return errors


def strip_jsonc_comments(value: str) -> str:
    output: list[str] = []
    in_string = False
    escaped = False
    index = 0
    while index < len(value):
        char = value[index]
        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            index += 1
        elif char == '"':
            in_string = True
            output.append(char)
            index += 1
        elif value[index : index + 2] == "//":
            index = value.find("\n", index)
            if index == -1:
                break
        else:
            output.append(char)
            index += 1
    return "".join(output)


def check_scenario_snippets() -> list[str]:
    sys.path.insert(0, str(ROOT / "backend"))
    from app.scenarios.models import ScenarioDefinition
    from pydantic import ValidationError

    guide = (ROOT / "backend/docs/scenario-authoring.md").read_text(encoding="utf-8")
    blocks = re.findall(
        r"^```jsonc?\s*\n(.*?)^```\s*$", guide, re.MULTILINE | re.DOTALL
    )
    errors: list[str] = []
    if not blocks:
        return ["scenario-authoring guide contains no JSON snippets"]
    for number, block in enumerate(blocks, 1):
        try:
            ScenarioDefinition.model_validate(json.loads(strip_jsonc_comments(block)))
        except (json.JSONDecodeError, ValidationError) as error:
            errors.append(
                f"scenario-authoring JSON snippet {number} is invalid: {error}"
            )
    return errors


def main() -> int:
    errors = (
        check_markdown()
        + check_api_routes()
        + check_frontend_routes()
        + check_scenario_snippets()
    )
    if errors:
        print("Documentation checks failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(
        f"Documentation checks passed ({len(MARKDOWN_FILES)} Markdown files checked)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
