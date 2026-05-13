#!/usr/bin/env python3
"""Validate the gvo-skills repo before commit/push.

Empirical checks driven by past failures (notably the gvo-router 1024-char
overflow in commit a2db4d7). Pure stdlib + pyyaml. Side-effect free.

Exit codes:
  0 = all checks pass, no warnings
  1 = at least one FAIL (blocks commit)
  2 = warnings only (advisory)

Usage:
  python3 scripts/validate.py            # full repo scan
  python3 scripts/validate.py --quiet    # only print FAIL/WARN summary
  python3 scripts/validate.py --json     # machine-readable output

Designed to run in <5s on the full repo (~272 SKILL.md + 2 registries).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

try:
    import yaml
except ImportError:
    print("FAIL: pyyaml is required. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# claude.ai's per-skill description hard limit. Source: commit a2db4d7
# ("trim description to under claude.ai 1024-char limit").
DESC_HARD_LIMIT = 1024
DESC_WARN_FLOOR = 900  # warning zone: 900..1023

REPO_ROOT = Path(__file__).resolve().parent.parent
ROOT_REGISTRY = REPO_ROOT / "registry.json"
NEXUS_REGISTRY = REPO_ROOT / "skills" / "nexus" / "registry.json"
SKILLS_DIR = REPO_ROOT / "skills"


@dataclass
class Finding:
    level: str           # "FAIL" | "WARN" | "INFO"
    code: str            # short stable identifier, e.g. "DESC_OVER_LIMIT"
    path: str            # absolute file path
    message: str
    context: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "code": self.code,
            "path": self.path,
            "message": self.message,
            "context": self.context,
        }


def parse_frontmatter(content: str) -> tuple[dict | None, str | None]:
    """Return (parsed_yaml, error). Either side may be None."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?", content, re.DOTALL)
    if not m:
        return None, "no YAML frontmatter (missing leading ---/--- block)"
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as e:
        return None, f"YAML parse error: {e}"
    if not isinstance(data, dict):
        return None, f"frontmatter is not a mapping (got {type(data).__name__})"
    return data, None


def check_skill_file(skill_md: Path) -> list[Finding]:
    findings: list[Finding] = []
    try:
        content = skill_md.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return [Finding("FAIL", "READ_ERROR", str(skill_md), f"cannot read file: {e}")]

    fm, err = parse_frontmatter(content)
    if err:
        findings.append(Finding("FAIL", "BAD_FRONTMATTER", str(skill_md), err))
        return findings

    name = fm.get("name")
    desc = fm.get("description")
    dir_name = skill_md.parent.name

    if not name:
        findings.append(Finding(
            "FAIL", "MISSING_NAME", str(skill_md),
            "frontmatter missing 'name' field",
        ))
    elif name != dir_name:
        findings.append(Finding(
            "FAIL", "NAME_DIR_MISMATCH", str(skill_md),
            f"name '{name}' does not match directory '{dir_name}'",
            context={"name": name, "dir": dir_name},
        ))

    if not desc:
        findings.append(Finding(
            "FAIL", "MISSING_DESCRIPTION", str(skill_md),
            "frontmatter missing 'description' field",
        ))
    else:
        desc_str = str(desc)
        n = len(desc_str)
        if n > DESC_HARD_LIMIT:
            findings.append(Finding(
                "FAIL", "DESC_OVER_LIMIT", str(skill_md),
                f"description is {n} chars; claude.ai limit is {DESC_HARD_LIMIT}",
                context={"length": n, "limit": DESC_HARD_LIMIT, "overage": n - DESC_HARD_LIMIT},
            ))
        elif n >= DESC_WARN_FLOOR:
            findings.append(Finding(
                "WARN", "DESC_NEAR_LIMIT", str(skill_md),
                f"description is {n} chars; within {DESC_HARD_LIMIT - n} of the {DESC_HARD_LIMIT} limit",
                context={"length": n, "limit": DESC_HARD_LIMIT, "headroom": DESC_HARD_LIMIT - n},
            ))

    return findings


def check_registry(registry_path: Path, repo_root: Path, optional: bool = False) -> tuple[list[Finding], list[dict]]:
    """Return (findings, parsed_skills_list). skills_list is empty on parse failure.

    If `optional` is True and the file does not exist, no findings are emitted. This is
    used for the legacy root `registry.json` which was deleted in favor of the canonical
    `skills/nexus/registry.json`.
    """
    findings: list[Finding] = []
    if not registry_path.exists():
        if optional:
            return [], []
        return [Finding("FAIL", "REGISTRY_MISSING", str(registry_path),
                        "registry file does not exist")], []

    try:
        raw = registry_path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        findings.append(Finding(
            "FAIL", "REGISTRY_BAD_JSON", str(registry_path),
            f"invalid JSON at line {e.lineno} col {e.colno}: {e.msg}",
        ))
        return findings, []
    except OSError as e:
        return [Finding("FAIL", "REGISTRY_READ_ERROR", str(registry_path),
                        f"cannot read: {e}")], []

    skills = data.get("skills", [])
    if not isinstance(skills, list):
        findings.append(Finding(
            "FAIL", "REGISTRY_BAD_SHAPE", str(registry_path),
            "'skills' field is not a list",
        ))
        return findings, []

    # Resolve every path; registry paths are relative to the registry's parent dir.
    registry_dir = registry_path.parent
    for idx, entry in enumerate(skills):
        if not isinstance(entry, dict):
            findings.append(Finding(
                "FAIL", "REGISTRY_BAD_ENTRY", str(registry_path),
                f"entry [{idx}] is not an object",
                context={"index": idx},
            ))
            continue

        name = entry.get("name", f"<entry[{idx}]>")
        path_str = entry.get("path")
        if not path_str:
            findings.append(Finding(
                "FAIL", "REGISTRY_NO_PATH", str(registry_path),
                f"entry '{name}' has no 'path'",
                context={"name": name, "index": idx},
            ))
        else:
            resolved = (registry_dir / path_str).resolve()
            if not resolved.exists():
                findings.append(Finding(
                    "FAIL", "REGISTRY_DEAD_PATH", str(registry_path),
                    f"entry '{name}': path resolves to non-existent file",
                    context={"name": name, "path": path_str, "resolved": str(resolved)},
                ))

        triggers = entry.get("triggers")
        if triggers is None or (isinstance(triggers, list) and len(triggers) == 0):
            findings.append(Finding(
                "WARN", "REGISTRY_EMPTY_TRIGGERS", str(registry_path),
                f"entry '{name}' has empty triggers — nexus won't surface it",
                context={"name": name},
            ))

    return findings, skills


def cross_check_registries(root_skills: list[dict], nexus_skills: list[dict]) -> list[Finding]:
    """Informational: surface entries in only one of the two registries."""
    findings: list[Finding] = []
    root_names = {s.get("name") for s in root_skills if isinstance(s, dict) and s.get("name")}
    nexus_names = {s.get("name") for s in nexus_skills if isinstance(s, dict) and s.get("name")}
    only_root = sorted(root_names - nexus_names)
    only_nexus = sorted(nexus_names - root_names)

    if only_root:
        findings.append(Finding(
            "INFO", "REG_ONLY_ROOT", str(ROOT_REGISTRY),
            f"{len(only_root)} entr{'y' if len(only_root)==1 else 'ies'} in root registry but not nexus",
            context={"names": only_root[:10], "total": len(only_root)},
        ))
    if only_nexus:
        findings.append(Finding(
            "INFO", "REG_ONLY_NEXUS", str(NEXUS_REGISTRY),
            f"{len(only_nexus)} entr{'y' if len(only_nexus)==1 else 'ies'} in nexus registry but not root",
            context={"names": only_nexus[:10], "total": len(only_nexus)},
        ))
    return findings


def iter_skill_files() -> Iterable[Path]:
    if not SKILLS_DIR.exists():
        return
    yield from SKILLS_DIR.rglob("SKILL.md")


def print_human(findings: list[Finding], elapsed: float, quiet: bool) -> None:
    by_level: dict[str, list[Finding]] = {"FAIL": [], "WARN": [], "INFO": []}
    for f in findings:
        by_level.setdefault(f.level, []).append(f)

    if not quiet:
        for level in ("FAIL", "WARN", "INFO"):
            for f in by_level[level]:
                rel = Path(f.path).relative_to(REPO_ROOT) if f.path.startswith(str(REPO_ROOT)) else Path(f.path)
                print(f"[{level}] [{f.code}] {rel}: {f.message}")

    summary = (
        f"validate.py: {len(by_level['FAIL'])} FAIL, "
        f"{len(by_level['WARN'])} WARN, "
        f"{len(by_level['INFO'])} INFO "
        f"({elapsed:.2f}s)"
    )
    print(summary)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--quiet", action="store_true", help="only print the summary line")
    p.add_argument("--json", action="store_true", help="emit JSON findings to stdout")
    args = p.parse_args()

    t0 = time.perf_counter()
    findings: list[Finding] = []

    for skill_md in iter_skill_files():
        findings.extend(check_skill_file(skill_md))

    root_findings, root_skills = check_registry(ROOT_REGISTRY, REPO_ROOT, optional=True)
    nexus_findings, nexus_skills = check_registry(NEXUS_REGISTRY, REPO_ROOT)
    findings.extend(root_findings)
    findings.extend(nexus_findings)
    # Only run cross-check if both registries are present. With root deleted, the
    # comparison would always report every nexus entry as "only in nexus" — useless noise.
    if root_skills and nexus_skills:
        findings.extend(cross_check_registries(root_skills, nexus_skills))

    elapsed = time.perf_counter() - t0

    if args.json:
        print(json.dumps({
            "elapsed_seconds": round(elapsed, 3),
            "findings": [f.to_dict() for f in findings],
            "summary": {
                "fail": sum(1 for f in findings if f.level == "FAIL"),
                "warn": sum(1 for f in findings if f.level == "WARN"),
                "info": sum(1 for f in findings if f.level == "INFO"),
            },
        }, indent=2))
    else:
        print_human(findings, elapsed, args.quiet)

    has_fail = any(f.level == "FAIL" for f in findings)
    has_warn = any(f.level == "WARN" for f in findings)
    if has_fail:
        return 1
    if has_warn:
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
