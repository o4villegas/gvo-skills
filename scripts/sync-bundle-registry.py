#!/usr/bin/env python3
"""Sync a third-party skill bundle into nexus/registry.json.

Three modes:
  audit  <bundle-path>           : Print collision report + net-new candidates.
  stub   <bundle-path> [--out F] : Write skeleton registry entries to FILE
                                   (default: candidates.json) with triggers=[]
                                   so a human can fill them in.
  apply  <file>                  : Append entries from FILE to registry.json
                                   (skips name-collisions with the existing
                                   registry, validates JSON before write).

Curation is a human step. This script automates inventory + path/id boilerplate
+ collision checks. Triggers MUST be filled by hand for nexus to surface a skill.

Plugin-collision list is embedded — derived from the harness's available-skills
section. Update PLUGIN_SKILLS as Anthropic ships new plugin skills.
"""
import argparse
import json
import os
import re
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
REGISTRY = REPO_ROOT / "skills" / "nexus" / "registry.json"

# Plugin skills available via the Claude Code harness. Skills with these names
# in a bundle are skipped — they're already wired into your environment.
PLUGIN_SKILLS = {
    "update-config", "keybindings-help", "simplify", "fewer-permission-prompts",
    "loop", "schedule", "claude-api", "agent-introspection-debugging",
    "agent-sort", "agent-teams", "apex", "api-design", "article-writing",
    "backend-patterns", "brand-voice", "bun-runtime", "claude-code-kit",
    "cloudflare-deploy", "coding-standards", "conductor", "configure-ecc",
    "content-engine", "continuous-learning", "continuous-learning-v2",
    "crosspost", "deep-research", "deployment-patterns", "dmux-workflows",
    "docker-patterns", "documentation-lookup", "e2e-testing", "eval-harness",
    "everything-claude-code", "everything-data", "exa-search", "fal-ai-media",
    "from-better-prompt", "from-prompter", "from-skill-forge",
    "frontend-design", "frontend-patterns", "frontend-slides",
    "full-stack-orchestration", "github-ops", "hookify-rules",
    "investor-materials", "investor-outreach", "iterative-retrieval",
    "kc-trivia-work", "kcc-scout", "market-research", "mcp-server-patterns",
    "nextjs-turbopack", "nexus", "pdf", "plankton-code-quality",
    "postgres-patterns", "product-capability", "research-lookup",
    "review-hunter", "runpod", "runpod-workflow", "search-first",
    "security-review", "skill-stocktake", "strategic-compact", "tdd-workflow",
    "verification-loop", "video-editing", "videodb", "x-api", "xlsx",
    "annotate", "fill-form", "open", "sign", "view-pdf",
    "generate-account-plan", "weekly-brief", "new-sdk-app",
    "revise-claude-md", "kc-trivia", "theme-factory", "kc-pulse",
    "ux-diagnostic", "internal-comms", "skill-creator", "web-artifacts-builder",
    "pptx", "scorecard-sync", "setup-cowork", "doc-coauthoring",
    "algorithmic-art", "brand-guidelines", "from-desktop",
    "financial-data-translator", "docx", "mcp-builder", "canvas-design",
    "from-kc-records", "consolidate-memory", "cowork-plugin-customizer",
    "create-cowork-plugin", "sox-testing", "variance-analysis",
    "reconciliation", "journal-entry-prep", "audit-support",
    "financial-statements", "close-management", "journal-entry",
    "user-research", "accessibility-review", "research-synthesis",
    "design-system", "design-handoff", "design-critique", "ux-copy",
    "account-research", "weekly-prep-brief", "prospect", "contact-research",
    "call-prep", "compose-outreach", "architecture", "standup",
    "incident-response", "testing-strategy", "documentation", "tech-debt",
    "deploy-checklist", "debug", "system-design", "code-review",
    "vendor-review", "process-doc", "status-report", "runbook",
    "compliance-tracking", "risk-assessment", "change-request",
    "capacity-plan", "process-optimization", "init", "review",
}


def extract_description(content):
    """Extract description from YAML frontmatter or inline 'description:' line."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if m:
        d = re.search(r"^description:\s*(.+?)(?=\n\w+:|\Z)", m.group(1),
                      re.MULTILINE | re.DOTALL)
        if d:
            return d.group(1).strip().strip('"\'').replace("\n", " ")
    for line in content.splitlines()[:30]:
        m2 = re.match(r"^\s*description:\s*(.+)$", line)
        if m2:
            return m2.group(1).strip().strip('"\'')
    return ""


def extract_name(content, fallback):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if m:
        n = re.search(r"^name:\s*(.+?)$", m.group(1), re.MULTILINE)
        if n:
            return n.group(1).strip().strip('"\'')
    return fallback


def walk_bundle(bundle_path):
    """Return list of {name, description, abs_path, rel_to_bundle} for every SKILL.md found."""
    bundle_path = Path(bundle_path).resolve()
    skills = []
    for sm in bundle_path.rglob("SKILL.md"):
        with open(sm, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        rel = sm.relative_to(bundle_path)
        name = extract_name(content, sm.parent.name)
        desc = extract_description(content)
        skills.append({
            "name": name,
            "description": desc,
            "abs_path": str(sm),
            "rel_to_bundle": str(rel).replace("\\", "/"),
        })
    return skills


def load_registry():
    with open(REGISTRY, "r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(reg):
    reg["generated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(REGISTRY, "w", encoding="utf-8") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)
    # Validate by re-reading
    with open(REGISTRY, "r", encoding="utf-8") as f:
        json.load(f)


def cmd_audit(args):
    skills = walk_bundle(args.bundle)
    reg = load_registry()
    nexus_names = {s["name"] for s in reg["skills"]}
    print(f"Bundle: {args.bundle}")
    print(f"Total SKILL.md found: {len(skills)}")
    plg = [s for s in skills if s["name"] in PLUGIN_SKILLS]
    nex = [s for s in skills if s["name"] in nexus_names]
    new = [s for s in skills
           if s["name"] not in PLUGIN_SKILLS and s["name"] not in nexus_names]
    print(f"  Collide with plugin:         {len(plg)}")
    print(f"  Collide with existing nexus: {len(nex)}")
    print(f"  Net-new candidates:          {len(new)}")
    if args.verbose:
        print("\n=== Net-new candidates ===")
        for s in new:
            print(f"  {s['name']:35s} | {s['description'][:120]}")
        if plg:
            print("\n=== Plugin collisions ===")
            for s in plg:
                print(f"  {s['name']:35s} (skip — plugin)")
        if nex:
            print("\n=== Nexus-registry collisions ===")
            for s in nex:
                print(f"  {s['name']:35s} (skip — already in registry)")


def cmd_stub(args):
    skills = walk_bundle(args.bundle)
    reg = load_registry()
    nexus_names = {s["name"] for s in reg["skills"]}
    bundle_name = Path(args.bundle).resolve().name
    # Path relative to nexus dir = "../<bundle-name>/<rel-to-bundle>"
    nexus_dir = REPO_ROOT / "skills" / "nexus"
    bundle_dir = Path(args.bundle).resolve()
    try:
        rel_bundle = bundle_dir.relative_to(REPO_ROOT / "skills")
        path_prefix = f"../{rel_bundle.as_posix()}"
    except ValueError:
        # Bundle outside skills/, use absolute path - user fixes manually
        path_prefix = str(bundle_dir).replace("\\", "/")
    out = []
    for s in skills:
        if s["name"] in PLUGIN_SKILLS or s["name"] in nexus_names:
            continue
        # Truncate verbose descriptions
        desc = s["description"]
        if len(desc) > 280:
            desc = desc[:280] + "..."
        out.append({
            "id": f"{s['name']}__imp_{secrets.token_hex(4)}",
            "name": s["name"],
            "description": desc,
            "path": f"{path_prefix}/{s['rel_to_bundle']}",
            "category": "uncategorized",
            "tags": [],
            "triggers": [],
            "isActive": True,
            "source": bundle_name,
        })
    output_path = Path(args.out)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"Wrote {len(out)} candidate entries to {output_path}")
    print("Next steps:")
    print("  1. Edit the file: set 'category' and 'triggers' for each entry.")
    print("  2. Delete entries you don't want.")
    print(f"  3. Run: {Path(__file__).name} apply {output_path}")


def cmd_apply(args):
    with open(args.file, "r", encoding="utf-8") as f:
        candidates = json.load(f)
    reg = load_registry()
    existing = {s["name"] for s in reg["skills"]}
    appended, skipped = [], []
    for c in candidates:
        if not c.get("triggers"):
            print(f"WARN: '{c['name']}' has empty triggers — nexus won't match it.")
        if c["name"] in existing:
            skipped.append(c["name"])
            continue
        reg["skills"].append(c)
        appended.append(c["name"])
    save_registry(reg)
    print(f"Appended: {len(appended)}")
    print(f"Skipped (already in registry): {len(skipped)}")
    if appended:
        print(f"  Sample: {appended[:5]}")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("audit", help="print collision report + net-new candidates")
    a.add_argument("bundle", help="path to bundle root (containing skill subdirs)")
    a.add_argument("-v", "--verbose", action="store_true", help="list each skill")
    a.set_defaults(func=cmd_audit)
    s = sub.add_parser("stub", help="write skeleton entries for human curation")
    s.add_argument("bundle", help="path to bundle root")
    s.add_argument("--out", default="candidates.json", help="output file")
    s.set_defaults(func=cmd_stub)
    ap = sub.add_parser("apply", help="merge curated entries into registry.json")
    ap.add_argument("file", help="JSON file produced by stub + edited by hand")
    ap.set_defaults(func=cmd_apply)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
