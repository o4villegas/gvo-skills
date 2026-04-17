#!/usr/bin/env bash
# gvo-skills/sync.sh — One-command sync for any environment
# Usage: ./sync.sh [--force]
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_LINK="$HOME/.claude/skills"

echo "=== gvo-skills sync ==="
echo "Repo:   $REPO_DIR"
echo "Target: $SKILLS_LINK"
echo ""

# 1. Pull latest from remote
echo "[1/3] Pulling latest..."
cd "$REPO_DIR"
if git remote get-url origin &>/dev/null; then
    git pull --ff-only origin main 2>/dev/null || {
        echo "  WARN: ff-only pull failed (local changes?). Run 'git pull' manually."
    }
else
    echo "  SKIP: no remote configured yet"
fi

# 2. Verify symlink
echo "[2/3] Checking symlink..."
if [ -L "$SKILLS_LINK" ]; then
    current_target="$(readlink -f "$SKILLS_LINK")"
    expected_target="$(readlink -f "$REPO_DIR/skills")"
    if [ "$current_target" = "$expected_target" ]; then
        echo "  OK: $SKILLS_LINK -> $REPO_DIR/skills"
    else
        echo "  WARN: symlink points to $current_target (expected $expected_target)"
        echo "  Run setup.sh to fix"
    fi
elif [ -d "$SKILLS_LINK" ]; then
    echo "  WARN: $SKILLS_LINK is a real directory, not a symlink"
    echo "  Run setup.sh to migrate"
else
    echo "  MISSING: $SKILLS_LINK does not exist"
    echo "  Run setup.sh to create"
fi

# 3. Inventory
echo "[3/3] Skill inventory:"
skill_count=$(find "$REPO_DIR/skills" -maxdepth 2 -name "SKILL.md" | wc -l)
registry_count=$(grep -c '^      "name":' "$REPO_DIR/registry.json" 2>/dev/null || echo "?")
echo "  SKILL.md files:    $skill_count"
echo "  Registry entries:  $registry_count"
echo ""
echo "Done."
