#!/usr/bin/env python3
"""
score_calibrator.py — Threshold calibration for kcc-scout opportunity scoring.

Usage:
    python score_calibrator.py <scored.json>

Input format (scored.json):
    [
        {"name": "...", "score": {"fit": 3, "proximity": 3, "reach": 2, "angle": 2,
                                  "total": 10}, "...": "..."},
        ...
    ]
    OR (alternate flat format):
    [
        {"name": "...", "total_score": 10, "...": "..."},
        ...
    ]

Output to stdout: a recommendation string and distribution summary.

Recommendation logic:
- Target: 4-10 items at threshold or above (sweet spot for human review)
- If >10 at current threshold → recommend raising
- If <4 at current threshold → recommend lowering
- If 4-10 → keep current threshold
- Threshold floor: 5 (below this, signal-to-noise is too poor)
- Threshold ceiling: 10 (above this, too aggressive — likely missing real opportunities)
"""

import json
import sys
from collections import Counter

DEFAULT_THRESHOLD = 7
TARGET_MIN = 4
TARGET_MAX = 10
THRESHOLD_FLOOR = 5
THRESHOLD_CEILING = 10


def get_total_score(item: dict) -> int:
    """Extract total score, supporting both nested and flat formats."""
    if "score" in item and isinstance(item["score"], dict):
        return item["score"].get("total", 0)
    if "total_score" in item:
        return item["total_score"]
    if "total" in item:
        return item["total"]
    return 0


def analyze_distribution(scores: list) -> Counter:
    """Return a Counter of how many items fall at each integer score."""
    return Counter(scores)


def format_distribution(dist: Counter, max_score: int = 12) -> str:
    """Render distribution as a horizontal bar chart in stderr-friendly format."""
    lines = []
    for s in range(max_score, -1, -1):
        n = dist.get(s, 0)
        bar = "█" * n
        lines.append(f"  {s:2d}/12  {n:3d}  {bar}")
    return "\n".join(lines)


def recommend(dist: Counter, current_threshold: int) -> dict:
    """
    Given a score distribution and current threshold, recommend an adjustment.
    Returns dict with: recommendation, current_count, suggested_threshold, reason.
    """
    at_or_above = sum(n for s, n in dist.items() if s >= current_threshold)

    result = {
        "current_threshold": current_threshold,
        "current_count_at_threshold": at_or_above,
        "target_range": f"{TARGET_MIN}-{TARGET_MAX}",
    }

    if TARGET_MIN <= at_or_above <= TARGET_MAX:
        result["recommendation"] = "keep"
        result["suggested_threshold"] = current_threshold
        result["reason"] = (
            f"{at_or_above} items at ≥{current_threshold}/12 — within target "
            f"range ({TARGET_MIN}-{TARGET_MAX}). Threshold is well-calibrated."
        )
        return result

    if at_or_above > TARGET_MAX:
        # Too many — try raising threshold
        for new_t in range(current_threshold + 1, THRESHOLD_CEILING + 1):
            new_count = sum(n for s, n in dist.items() if s >= new_t)
            if TARGET_MIN <= new_count <= TARGET_MAX:
                result["recommendation"] = "raise"
                result["suggested_threshold"] = new_t
                result["reason"] = (
                    f"{at_or_above} items at ≥{current_threshold}/12 (above target). "
                    f"Raising to ≥{new_t}/12 yields {new_count} items — within target."
                )
                return result
        # Even ceiling still too many
        result["recommendation"] = "raise"
        result["suggested_threshold"] = THRESHOLD_CEILING
        result["reason"] = (
            f"{at_or_above} items at ≥{current_threshold}/12 — many strong candidates. "
            f"Even at threshold ceiling {THRESHOLD_CEILING}, signal is dense. "
            f"Consider raising or accepting larger output."
        )
        return result

    # Too few — try lowering
    for new_t in range(current_threshold - 1, THRESHOLD_FLOOR - 1, -1):
        new_count = sum(n for s, n in dist.items() if s >= new_t)
        if TARGET_MIN <= new_count <= TARGET_MAX:
            result["recommendation"] = "lower"
            result["suggested_threshold"] = new_t
            result["reason"] = (
                f"Only {at_or_above} items at ≥{current_threshold}/12 (below target). "
                f"Lowering to ≥{new_t}/12 yields {new_count} items — within target."
            )
            return result
    # Even floor still too few
    result["recommendation"] = "lower"
    result["suggested_threshold"] = THRESHOLD_FLOOR
    floor_count = sum(n for s, n in dist.items() if s >= THRESHOLD_FLOOR)
    result["reason"] = (
        f"Only {at_or_above} items at ≥{current_threshold}/12. "
        f"Even at threshold floor {THRESHOLD_FLOOR}, only {floor_count} items qualify — "
        f"this run is sparse. Treat output as exploratory; consider re-running with "
        f"wider date window or additional sources."
    )
    return result


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(
            "Usage: python score_calibrator.py <scored.json> [current_threshold]",
            file=sys.stderr,
        )
        sys.exit(1)

    path = sys.argv[1]
    current_t = int(sys.argv[2]) if len(sys.argv) == 3 else DEFAULT_THRESHOLD

    with open(path) as f:
        items = json.load(f)

    scores = [get_total_score(item) for item in items if get_total_score(item) > 0]
    if not scores:
        print("No scored items found in input.", file=sys.stderr)
        sys.exit(1)

    dist = analyze_distribution(scores)
    rec = recommend(dist, current_t)

    print(f"Total scored items: {len(scores)}")
    print(f"\nDistribution:\n{format_distribution(dist)}")
    print(f"\nCurrent threshold: ≥{rec['current_threshold']}/12")
    print(f"Items at or above threshold: {rec['current_count_at_threshold']}")
    print(f"Target range: {rec['target_range']} items")
    print(f"\nRecommendation: {rec['recommendation'].upper()}")
    print(f"Suggested threshold: ≥{rec['suggested_threshold']}/12")
    print(f"Reason: {rec['reason']}")


if __name__ == "__main__":
    main()
