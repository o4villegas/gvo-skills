#!/usr/bin/env python3
"""
Deduplicate events across sources by normalized (artist, date, venue) tuple.

Usage:
    python dedup_events.py <events.json>

Input format (events.json):
    [
        {"name": "The Happy Fits", "date": "2026-06-12", "venue": "Jannus Live",
         "source": "bandsintown.com/...", "...": "..."},
        ...
    ]

Output: deduped list (same format) with `sources` field merged into a list.

Dedup logic:
- Normalize name: lowercase, strip leading "the ", strip whitespace, drop punctuation
- Match on (normalized_name, date)
- Venue is informational; sometimes sources list slightly different venues
  (e.g., "Capitol Theatre" vs "Bilheimer Capitol Theatre"), so we don't require exact match
- When merging, keep all source URLs and prefer the first source's other metadata
"""

import json
import re
import sys
from collections import OrderedDict


def normalize_name(name: str) -> str:
    """Lowercase, strip articles, drop punctuation, collapse whitespace."""
    if not name:
        return ""
    s = name.lower().strip()
    # Strip leading "the "
    if s.startswith("the "):
        s = s[4:]
    # Drop punctuation except internal hyphens (which sometimes carry meaning)
    s = re.sub(r"[^\w\s\-]", "", s)
    # Collapse whitespace
    s = re.sub(r"\s+", " ", s).strip()
    return s


def dedup_events(events: list) -> list:
    """
    Group events by (normalized_name, date). Merge sources within each group.
    Preserve first-seen metadata; collect all source URLs.
    """
    grouped = OrderedDict()

    for event in events:
        name = event.get("name", "")
        date = event.get("date", "")
        key = (normalize_name(name), date)

        if not name or not date:
            # Skip malformed entries; log to stderr
            print(f"WARN: skipping event with missing name/date: {event}", file=sys.stderr)
            continue

        if key not in grouped:
            # First time seeing this event — initialize
            grouped[key] = dict(event)
            grouped[key]["sources"] = [event.get("source", "")]
        else:
            # Already seen — merge sources
            existing_sources = grouped[key]["sources"]
            new_source = event.get("source", "")
            if new_source and new_source not in existing_sources:
                existing_sources.append(new_source)
            # If existing record has missing fields and new one has them, fill in
            for field in ("venue", "time", "url", "description"):
                if not grouped[key].get(field) and event.get(field):
                    grouped[key][field] = event[field]

    # Strip the now-redundant "source" field; canonical source list lives in "sources"
    result = []
    for record in grouped.values():
        record.pop("source", None)
        result.append(record)

    return result


def main():
    if len(sys.argv) != 2:
        print("Usage: python dedup_events.py <events.json>", file=sys.stderr)
        sys.exit(1)

    path = sys.argv[1]
    with open(path) as f:
        events = json.load(f)

    if not isinstance(events, list):
        print("ERROR: input must be a JSON list of events", file=sys.stderr)
        sys.exit(1)

    deduped = dedup_events(events)

    print(json.dumps(deduped, indent=2))
    print(
        f"\nDedup: {len(events)} input → {len(deduped)} unique "
        f"({len(events) - len(deduped)} duplicates removed)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
