#!/usr/bin/env bash
# gvo-skills/setup.sh — First-time setup per environment
# Creates the symlink from ~/.claude/skills -> this repo's skills/ directory
# Safe: backs up existing skills directory before replacing
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_DIR="$REPO_DIR/skills"
SKILLS_LINK="$HOME/.claude/skills"
BACKUP_DIR="$HOME/.claude/skills.bak.$(date +%Y%m%d-%H%M%S)"

echo "=== gvo-skills setup ==="
echo "Repo:       $REPO_DIR"
echo "Skills dir: $SKILLS_DIR"
echo "Link path:  $SKILLS_LINK"
echo ""

# Ensure ~/.claude exists
mkdir -p "$HOME/.claude"

# Handle existing skills directory
if [ -L "$SKILLS_LINK" ]; then
    current="$(readlink "$SKILLS_LINK")"
    echo "Existing symlink found: $SKILLS_LINK -> $current"
    if [ "$(readlink -f "$SKILLS_LINK")" = "$(readlink -f "$SKILLS_DIR")" ]; then
        echo "Already correctly linked. Nothing to do."
        exit 0
    fi
    echo "Removing old symlink..."
    rm "$SKILLS_LINK"
elif [ -d "$SKILLS_LINK" ]; then
    echo "Existing directory found at $SKILLS_LINK"
    echo "Backing up to $BACKUP_DIR ..."
    mv "$SKILLS_LINK" "$BACKUP_DIR"
    echo "  Backed up: $BACKUP_DIR"
fi

# Create symlink
echo ""
echo "Creating symlink: $SKILLS_LINK -> $SKILLS_DIR"
ln -s "$SKILLS_DIR" "$SKILLS_LINK"

# Verify
if [ -L "$SKILLS_LINK" ] && [ -d "$SKILLS_LINK/nexus" ]; then
    echo ""
    echo "SUCCESS: Skills linked."
    echo ""
    skill_count=$(find "$SKILLS_DIR" -maxdepth 2 -name "SKILL.md" | wc -l)
    echo "  $skill_count skills available"
    echo "  Nexus registry: $(python3 -c "import json; print(len(json.load(open('$REPO_DIR/registry.json'))['skills']))" 2>/dev/null || echo '?') entries"

    if [ -d "$BACKUP_DIR" ]; then
        echo ""
        echo "NOTE: Your old skills are backed up at:"
        echo "  $BACKUP_DIR"
        echo "  Delete when you're confident everything works."
    fi
else
    echo ""
    echo "ERROR: Symlink verification failed."
    echo "  Expected $SKILLS_LINK/nexus to exist."
    exit 1
fi
