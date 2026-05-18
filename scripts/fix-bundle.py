#!/usr/bin/env python3
"""One-shot patcher for upstream frontmatter bugs in the awesome-claude-corporate-skills bundle.

Patches three classes of issue (all originally surfaced by validate.py FAILs):
  1. BAD_FRONTMATTER     — file has description as a body paragraph, no YAML frontmatter
  2. MISSING_DESCRIPTION — frontmatter present but `description:` field absent
  3. NAME_DIR_MISMATCH   — frontmatter `name` does not match directory name
                           (only the non-disambiguator cases; -common-room / -apollo
                           cases are handled in validate.py's DIR_NAME_DISAMBIGUATORS)

Originally applied 2026-05-18 to bring `python3 scripts/validate.py` from 42 FAIL → 0 FAIL.
Idempotent — re-running on already-patched files is a no-op.

Re-run after a vendor refresh of `awesome-claude-corporate-skills-main/`:
    python3 scripts/fix-bundle.py
Then re-run validate.py to confirm.

See `skills/awesome-claude-corporate-skills-main/PATCHES.md` for the change manifest
and a pre-filled upstream issue body.

Usage:
    python3 scripts/fix-bundle.py           # default: bundle dir auto-detected
    python3 scripts/fix-bundle.py <path>    # override bundle dir
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BUNDLE = REPO_ROOT / "skills" / "awesome-claude-corporate-skills-main"

# Files known to ship with description in body but no YAML frontmatter.
BAD_FRONTMATTER_FILES: list[str] = [
    "02-finance-accounting/model-update/SKILL.md",
    "02-finance-accounting/deal-tracker/SKILL.md",
    "02-finance-accounting/teaser/SKILL.md",
    "02-finance-accounting/unit-economics/SKILL.md",
    "02-finance-accounting/dd-checklist/SKILL.md",
    "02-finance-accounting/client-report/SKILL.md",
    "02-finance-accounting/client-review/SKILL.md",
    "02-finance-accounting/deal-screening/SKILL.md",
    "02-finance-accounting/ic-memo/SKILL.md",
    "02-finance-accounting/dd-meeting-prep/SKILL.md",
    "02-finance-accounting/investment-proposal/SKILL.md",
    "02-finance-accounting/merger-model/SKILL.md",
    "02-finance-accounting/buyer-list/SKILL.md",
    "02-finance-accounting/earnings-preview/SKILL.md",
    "02-finance-accounting/cim-builder/SKILL.md",
    "02-finance-accounting/tax-loss-harvesting/SKILL.md",
    "02-finance-accounting/portfolio-monitoring/SKILL.md",
    "02-finance-accounting/catalyst-calendar/SKILL.md",
    "02-finance-accounting/idea-generation/SKILL.md",
    "02-finance-accounting/value-creation-plan/SKILL.md",
    "02-finance-accounting/sector-overview/SKILL.md",
    "02-finance-accounting/financial-plan/SKILL.md",
    "02-finance-accounting/thesis-tracker/SKILL.md",
    "02-finance-accounting/portfolio-rebalance/SKILL.md",
    "02-finance-accounting/morning-note/SKILL.md",
    "02-finance-accounting/process-letter/SKILL.md",
    "02-finance-accounting/returns-analysis/SKILL.md",
    "02-finance-accounting/deal-sourcing/SKILL.md",
]

# Frontmatter present but missing description; description lives in body.
MISSING_DESC_FILES: list[str] = [
    "02-finance-accounting/check-model/SKILL.md",
]

# Frontmatter `name` doesn't match directory; rewrite name to match dir.
# These are unintentional upstream bugs — the -common-room/-apollo disambiguator
# cases are handled in validate.py's DIR_NAME_DISAMBIGUATORS, not here.
NAME_MISMATCH_FILES: list[str] = [
    "02-finance-accounting/spglobal-earnings-preview/SKILL.md",
    "02-finance-accounting/spglobal-tear-sheet/SKILL.md",
    "02-finance-accounting/strip-profile/SKILL.md",
    "02-finance-accounting/spglobal-funding-digest/SKILL.md",
    "02-finance-accounting/comps-analysis/SKILL.md",
    "08-it-engineering/software-architecture/SKILL.md",
    "07-operations/kaizen/SKILL.md",
    "03-human-resources/resume-generator/SKILL.md",
]


def extract_body_description(content: str) -> tuple[str | None, str]:
    """Find a `description: ...` line in the body (not in frontmatter).

    Returns (description_text, remaining_content_without_that_line). Heuristic:
    first paragraph-level line starting with `description:`; continuation captured
    until the first blank line / new H-heading / new YAML key.
    """
    lines = content.splitlines()
    desc_lines: list[str] = []
    consumed_idx: list[int] = []

    in_desc = False
    for i, line in enumerate(lines):
        if not in_desc:
            if line.strip().lower().startswith("description:"):
                in_desc = True
                first = line.split(":", 1)[1].strip()
                if first:
                    desc_lines.append(first)
                consumed_idx.append(i)
        else:
            stripped = line.strip()
            if not stripped:
                break
            if stripped.startswith("#") or stripped.startswith("---"):
                break
            if stripped.endswith(":") and not stripped.startswith("-"):
                break
            desc_lines.append(stripped)
            consumed_idx.append(i)

    if not desc_lines:
        return None, content

    description = " ".join(desc_lines)
    consumed_set = set(consumed_idx)
    last_consumed = max(consumed_idx)
    if last_consumed + 1 < len(lines) and lines[last_consumed + 1].strip() == "":
        consumed_set.add(last_consumed + 1)
    new_lines = [ln for i, ln in enumerate(lines) if i not in consumed_set]
    return description, "\n".join(new_lines)


def yaml_escape(s: str) -> str:
    """Minimal escape for YAML double-quoted scalar."""
    if '"' in s or "\\" in s:
        return s.replace("\\", "\\\\").replace('"', '\\"')
    return s


def patch_bad_frontmatter(path: Path, dir_name: str) -> tuple[bool, str]:
    """Add YAML frontmatter wrapping the body description. Idempotent."""
    content = path.read_text(encoding="utf-8")
    if content.startswith("---"):
        return False, "already has frontmatter"

    description, remaining = extract_body_description(content)
    if not description:
        return False, "no body description found — cannot derive frontmatter"

    escaped = yaml_escape(description)
    if '"' in escaped or escaped != description:
        new_frontmatter = (
            f'---\n'
            f'name: {dir_name}\n'
            f'description: "{escaped}"\n'
            f'---\n'
        )
    else:
        new_frontmatter = (
            f'---\n'
            f'name: {dir_name}\n'
            f'description: >\n'
            f'  {description}\n'
            f'---\n'
        )

    remaining = remaining.lstrip("\n")
    path.write_text(new_frontmatter + remaining, encoding="utf-8")
    return True, f"wrapped {len(description)}-char description in frontmatter"


def patch_missing_description(path: Path, dir_name: str) -> tuple[bool, str]:
    """Add a description field to existing frontmatter, sourced from body."""
    content = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not m:
        return False, "no frontmatter present (would need BAD_FRONTMATTER patch first)"
    fm_text = m.group(1)
    if re.search(r"^description:", fm_text, re.MULTILINE):
        return False, "description already present"

    body = content[m.end():]
    description, new_body = extract_body_description(body)
    if not description:
        return False, "no body description found"

    escaped = yaml_escape(description)
    if '"' in escaped or escaped != description:
        new_fm = fm_text + f'\ndescription: "{escaped}"'
    else:
        new_fm = fm_text + f'\ndescription: >\n  {description}'

    new_content = f"---\n{new_fm}\n---\n" + new_body.lstrip("\n")
    path.write_text(new_content, encoding="utf-8")
    return True, f"added {len(description)}-char description to frontmatter"


def patch_name_mismatch(path: Path, dir_name: str) -> tuple[bool, str]:
    """Rewrite the `name:` field in frontmatter to match the dir name."""
    content = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if not m:
        return False, "no frontmatter to patch"
    fm_text = m.group(1)
    name_match = re.search(r"^name:\s*(.+)$", fm_text, re.MULTILINE)
    if not name_match:
        return False, "no name field"
    current_name = name_match.group(1).strip().strip('"').strip("'")
    if current_name == dir_name:
        return False, "name already matches dir"

    new_fm = re.sub(
        r"^name:\s*.+$",
        f"name: {dir_name}",
        fm_text,
        count=1,
        flags=re.MULTILINE,
    )
    new_content = f"---\n{new_fm}\n---\n" + content[m.end():]
    path.write_text(new_content, encoding="utf-8")
    return True, f"renamed '{current_name}' -> '{dir_name}'"


def main() -> int:
    bundle = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_BUNDLE
    if not bundle.exists():
        print(f"FATAL: bundle dir not found at {bundle}", file=sys.stderr)
        return 1

    changes: list[tuple[str, str, str]] = []

    print(f"Bundle root: {bundle}")
    print(f"\n=== BAD_FRONTMATTER patches ({len(BAD_FRONTMATTER_FILES)} files) ===")
    for rel in BAD_FRONTMATTER_FILES:
        p = bundle / rel
        if not p.exists():
            print(f"  SKIP missing: {rel}")
            continue
        changed, msg = patch_bad_frontmatter(p, p.parent.name)
        print(f"  {'PATCHED' if changed else 'SKIP'} {rel}: {msg}")
        if changed:
            changes.append(("BAD_FRONTMATTER", rel, msg))

    print(f"\n=== MISSING_DESCRIPTION patches ({len(MISSING_DESC_FILES)} files) ===")
    for rel in MISSING_DESC_FILES:
        p = bundle / rel
        if not p.exists():
            print(f"  SKIP missing: {rel}")
            continue
        changed, msg = patch_missing_description(p, p.parent.name)
        print(f"  {'PATCHED' if changed else 'SKIP'} {rel}: {msg}")
        if changed:
            changes.append(("MISSING_DESCRIPTION", rel, msg))

    print(f"\n=== NAME_DIR_MISMATCH patches ({len(NAME_MISMATCH_FILES)} files) ===")
    for rel in NAME_MISMATCH_FILES:
        p = bundle / rel
        if not p.exists():
            print(f"  SKIP missing: {rel}")
            continue
        changed, msg = patch_name_mismatch(p, p.parent.name)
        print(f"  {'PATCHED' if changed else 'SKIP'} {rel}: {msg}")
        if changed:
            changes.append(("NAME_DIR_MISMATCH", rel, msg))

    print(f"\n=== TOTAL: {len(changes)} files patched ===")
    print(
        "\nNext: run `python3 scripts/validate.py` to confirm 0 FAIL.\n"
        "If you re-vendored the bundle, also consider filing the upstream PR.\n"
        "See `skills/awesome-claude-corporate-skills-main/PATCHES.md` for the\n"
        "pre-filled upstream issue body."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
