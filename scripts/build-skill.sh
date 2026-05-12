#!/usr/bin/env bash
# scripts/build-skill.sh — Package a skill into a claude.ai-compatible .zip
#
# Usage:
#   scripts/build-skill.sh <skill-name> [--out <dir>]
#   scripts/build-skill.sh --all       [--out <dir>]
#
# Produces dist/<skill>.zip with POSIX forward-slash paths so claude.ai's
# upload validator accepts it. PowerShell's Compress-Archive on Windows
# writes backslashes which claude.ai rejects with "Zip file contains
# path with invalid characters" — always build via this script (run it
# under WSL on Windows).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$REPO_DIR/skills"
OUT_DIR="$REPO_DIR/dist"
TARGET=""

while [ $# -gt 0 ]; do
    case "$1" in
        --out)
            OUT_DIR="$2"
            shift 2
            ;;
        --all)
            TARGET="__all__"
            shift
            ;;
        -h|--help)
            sed -n '2,12p' "$0"
            exit 0
            ;;
        -*)
            echo "ERROR: unknown flag: $1" >&2
            exit 2
            ;;
        *)
            if [ -n "$TARGET" ] && [ "$TARGET" != "__all__" ]; then
                echo "ERROR: multiple skill names given" >&2
                exit 2
            fi
            TARGET="$1"
            shift
            ;;
    esac
done

if [ -z "$TARGET" ]; then
    echo "ERROR: skill name required (or --all)" >&2
    sed -n '2,12p' "$0" >&2
    exit 2
fi

if ! command -v zip >/dev/null 2>&1; then
    echo "ERROR: 'zip' not found. Install with: apt install zip" >&2
    exit 1
fi

mkdir -p "$OUT_DIR"

build_one() {
    local name="$1"
    local src="$SKILLS_DIR/$name"
    local skill_md="$src/SKILL.md"
    local out="$OUT_DIR/$name.zip"

    if [ ! -d "$src" ]; then
        echo "ERROR: $src not found" >&2
        return 1
    fi
    if [ ! -f "$skill_md" ]; then
        echo "ERROR: $skill_md missing — claude.ai requires SKILL.md" >&2
        return 1
    fi

    rm -f "$out"
    (cd "$SKILLS_DIR" && zip -rq "$out" "$name" \
        -x "$name/.*" "$name/**/.*" \
           "$name/*.bak" "$name/**/*.bak" \
           "$name/__pycache__/*" "$name/**/__pycache__/*")

    if unzip -l "$out" | grep -q '\\'; then
        echo "ERROR: $out contains backslash paths (build broken)" >&2
        return 1
    fi

    local files
    files=$(unzip -l "$out" | tail -1 | awk '{print $2}')
    local bytes
    bytes=$(stat -c%s "$out" 2>/dev/null || stat -f%z "$out")
    printf "  built %-40s  %4s files  %8s bytes\n" "$out" "$files" "$bytes"
}

if [ "$TARGET" = "__all__" ]; then
    echo "Building all skills with SKILL.md → $OUT_DIR"
    count=0
    while IFS= read -r skill_md; do
        name="$(basename "$(dirname "$skill_md")")"
        if [ "$(dirname "$skill_md")" = "$SKILLS_DIR/$name" ]; then
            build_one "$name" || true
            count=$((count + 1))
        fi
    done < <(find "$SKILLS_DIR" -maxdepth 2 -name SKILL.md | sort)
    echo "Done: $count skill(s)."
else
    echo "Building $TARGET → $OUT_DIR"
    build_one "$TARGET"
fi
