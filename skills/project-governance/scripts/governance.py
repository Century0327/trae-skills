#!/usr/bin/env python3
"""Project governance workspace scaffold & registry validator.

Subcommands:
  init      Create AGENTS.md, index.md, LESSONS.md, session_handoff.md,
            CHANGELOG.md, VERSIONS.md, blacklist.json, whitelist.json
            from templates/.
  validate  Check that blacklist.json / whitelist.json conform to the schema.
  index     Refresh the "Root layout" section of index.md from a filesystem scan.

The script is deterministic and idempotent: it never overwrites existing files
unless --force is passed.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

TEMPLATE_FILES = [
    "AGENTS.md",
    "ARCHITECTURE.md",
    "PROJECT.md",
    "index.md",
    "LESSONS.md",
    "session_handoff.md",
    "CHANGELOG.md",
    "VERSIONS.md",
    "blacklist.json",
    "whitelist.json",
]

# Only placeholders that can be auto-filled are substituted; the rest stay
# as {{PLACEHOLDER}} for the user to fill in.
AUTO_PLACEHOLDERS = {
    "{{PROJECT_NAME}}": "My Project",
    "{{PROJECT_ROOT}}": ".",
    "{{DATE}}": date.today().isoformat(),
    "{{CHANGES}}": "Initial scaffold.",
}

SKIP_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules", ".venv", "venv", ".idea", ".vscode", "dist", "build",
}

BLACKLIST_REQUIRED = ["id", "reason", "permanent_ban", "alternative", "test_ref", "judge", "scope", "status"]
WHITELIST_REQUIRED = ["id", "score", "config", "test_ref", "judge", "last_verified", "scope", "status"]
VALID_STATUS = {"active", "superseded", "deprecated"}
VALID_JUDGE = {"ai", "human"}


def _templates_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "templates"


def cmd_init(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    if project_dir.exists() and not project_dir.is_dir():
        print(f"ERROR: project directory path is an existing file: {project_dir}")
        return 1
    project_dir.mkdir(parents=True, exist_ok=True)
    templates = _templates_dir()
    if not templates.is_dir():
        print(f"ERROR: templates directory not found: {templates}")
        print("HINT: keep templates/ next to scripts/ when copying this skill.")
        return 1

    if getattr(args, "project_name", None):
        AUTO_PLACEHOLDERS["{{PROJECT_NAME}}"] = args.project_name

    created, skipped = [], []
    for name in TEMPLATE_FILES:
        dst = project_dir / name
        if dst.is_dir():
            print(f"ERROR: target path is a directory, not a file: {dst}")
            return 1
        if dst.exists() and not args.force:
            skipped.append(name)
            continue
        src = templates / name
        if not src.exists():
            print(f"ERROR: template missing: {src}")
            return 1
        text = src.read_text(encoding="utf-8")
        for key, value in AUTO_PLACEHOLDERS.items():
            text = text.replace(key, value)
        dst.write_text(text, encoding="utf-8")
        created.append(name)

    print(f"Created {len(created)} governance files in {project_dir}")
    for name in created:
        print(f"  + {name}")
    if skipped:
        print(f"Skipped {len(skipped)} existing files (use --force to overwrite):")
        for name in skipped:
            print(f"  = {name}")
    return 0


def _validate_registry(path: Path, required: list[str], label: str) -> list[str]:
    errors = []
    if not path.exists():
        errors.append(f"{label}: file not found: {path}")
        return errors
    if not path.is_file():
        errors.append(f"{label}: not a regular file: {path}")
        return errors
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        errors.append(f"{label}: file is not valid UTF-8 text: {exc}")
        return errors
    except json.JSONDecodeError as exc:
        errors.append(f"{label}: invalid JSON at line {exc.lineno}: {exc.msg}")
        return errors
    if not isinstance(data, dict):
        errors.append(f"{label}: top-level JSON must be an object, got {type(data).__name__}")
        return errors

    entries = data.get(label)
    if not isinstance(entries, list):
        errors.append(f"{label}: top-level '{label}' must be a list")
        return errors

    seen_ids = set()
    for idx, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"{label}[{idx}]: entry must be an object")
            continue
        missing = [f for f in required if f not in entry]
        if missing:
            errors.append(f"{label}[{idx}]: missing required fields: {', '.join(missing)}")
        if "id" in entry:
            if not isinstance(entry["id"], str):
                errors.append(f"{label}[{idx}]: id must be a string, got {entry['id']!r}")
            elif entry["id"] in seen_ids:
                errors.append(f"{label}[{idx}]: duplicate id '{entry['id']}'")
            else:
                seen_ids.add(entry["id"])
        if "status" in entry and entry["status"] not in VALID_STATUS:
            errors.append(f"{label}[{idx}]: invalid status '{entry['status']}' (valid: {sorted(VALID_STATUS)})")
        if "judge" in entry and entry["judge"] not in VALID_JUDGE:
            errors.append(f"{label}[{idx}]: invalid judge '{entry['judge']}' (valid: {sorted(VALID_JUDGE)})")
        if label == "blacklist" and "permanent_ban" in entry and not isinstance(entry["permanent_ban"], bool):
            errors.append(f"{label}[{idx}]: permanent_ban must be a boolean, got {entry['permanent_ban']!r}")
        if label == "whitelist" and "score" in entry:
            score = entry["score"]
            if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 1:
                errors.append(f"{label}[{idx}]: score must be a number in [0, 1], got {score!r}")
    return errors


def cmd_validate(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    errors = []
    errors += _validate_registry(project_dir / "blacklist.json", BLACKLIST_REQUIRED, "blacklist")
    errors += _validate_registry(project_dir / "whitelist.json", WHITELIST_REQUIRED, "whitelist")
    if errors:
        print("VALIDATION FAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1
    print("VALIDATION PASSED: blacklist.json and whitelist.json conform to the schema.")
    return 0


def _build_tree(root: Path, max_depth: int) -> list[str]:
    lines = []

    def walk(path: Path, prefix: str, depth: int) -> None:
        if depth > max_depth:
            lines.append(f"{prefix}└── ...")
            return
        try:
            entries = sorted(
                (p for p in path.iterdir() if p.name not in SKIP_DIRS and not p.name.startswith(".")),
                key=lambda p: (p.is_file(), p.name.lower()),
            )
        except OSError:
            lines.append(f"{prefix}└── <unreadable>")
            return
        for i, entry in enumerate(entries):
            last = i == len(entries) - 1
            connector = "└── " if last else "├── "
            lines.append(f"{prefix}{connector}{entry.name}{'/' if entry.is_dir() else ''}")
            if entry.is_dir():
                walk(entry, prefix + ("    " if last else "│   "), depth + 1)

    walk(root, "", 0)
    return lines


def cmd_index(args: argparse.Namespace) -> int:
    project_dir = Path(args.project_dir).resolve()
    index_path = project_dir / "index.md"
    if not index_path.exists():
        print(f"ERROR: index.md not found: {index_path}")
        print("HINT: run 'governance.py init' first to scaffold the workspace.")
        return 1
    if not index_path.is_file():
        print(f"ERROR: index.md is not a regular file: {index_path}")
        return 1

    tree = _build_tree(project_dir, args.max_depth)
    section = "## Root layout\n```\n" + "\n".join(tree) + "\n```\n"

    try:
        text = index_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        print(f"ERROR: index.md is not valid UTF-8 text: {exc}")
        return 1
    start = text.find("## Root layout")
    end = text.find("## Change log")
    if start == -1 or end == -1 or end < start:
        print("ERROR: index.md must contain '## Root layout' before '## Change log' sections.")
        return 1
    new_text = text[:start] + section + text[end:]
    index_path.write_text(new_text, encoding="utf-8")
    print(f"Updated 'Root layout' in {index_path} ({len(tree)} lines).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="scaffold the governance workspace from templates")
    p_init.add_argument("--project-dir", required=True, help="target project directory")
    p_init.add_argument("--project-name", default="My Project", help="project name (default: My Project)")
    p_init.add_argument("--force", action="store_true", help="overwrite existing files")
    p_init.set_defaults(func=cmd_init)

    p_val = sub.add_parser("validate", help="validate blacklist.json / whitelist.json schema")
    p_val.add_argument("--project-dir", required=True, help="project directory containing the registries")
    p_val.set_defaults(func=cmd_validate)

    p_idx = sub.add_parser("index", help="refresh the Root layout section of index.md")
    p_idx.add_argument("--project-dir", required=True, help="project directory containing index.md")
    p_idx.add_argument("--max-depth", type=int, default=4, help="max tree depth (default: 4)")
    p_idx.set_defaults(func=cmd_index)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: unexpected failure: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
