#!/usr/bin/env python3
"""
Fetch and filter Reddit posts from one or more subreddits using the public
.json endpoint (no auth needed).

Usage:
    python parse_reddit.py r/tampa r/StPetersburgFL
    python parse_reddit.py r/tampa --min-score 50 --days 7

Filters applied:
- Minimum score (default 30) — reduces noise
- Posted within last N days (default 14)
- Drops posts whose title or selftext matches noise keywords
  (politics, lost-pet, complaints, sales spam, real-estate, etc.)
- Drops stickied posts (usually meta/rules)

Output: JSON list of relevant posts with title, score, url, subreddit, created_utc, permalink
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.request

# Keywords that indicate a post is not signal for KCC scouting
NOISE_KEYWORDS = {
    # Politics — frequent, high-volume, irrelevant to event scouting
    "no kings", "trump", "biden", "desantis", "republican", "democrat",
    "election", "vote", "ballot", "abortion", "second amendment",
    # Lost-and-found
    "lost dog", "lost cat", "missing pet", "found dog", "found cat",
    # Complaints / venting
    "rant", "vent", "fuck this", "anyone else hate",
    # Sales spam / real estate
    "for sale", "selling my", "looking to buy", "fsbo", "realtor",
    "rent my", "looking for roommate",
    # Service requests not relevant to events
    "recommendations for plumber", "dentist", "mechanic", "lawyer",
    # Storms / weather (unless tied to a specific event)
    "hurricane", "storm warning", "tornado",
}


def fetch_subreddit(subreddit: str, limit: int = 50) -> list:
    """
    Fetch hot posts from a subreddit via the public .json endpoint.
    Returns a list of post dicts (the raw "data" field of each post).
    """
    # Strip leading "r/" if present
    sub = subreddit.lstrip("/")
    if sub.startswith("r/"):
        sub = sub[2:]

    url = f"https://www.reddit.com/r/{sub}/hot.json?limit={limit}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "kcc-scout/2.0 (event scouting bot for KC Clearwater)"},
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"WARN: HTTP {e.code} fetching {url}", file=sys.stderr)
        return []
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as e:
        print(f"WARN: error fetching {url}: {e}", file=sys.stderr)
        return []

    children = data.get("data", {}).get("children", [])
    return [c.get("data", {}) for c in children]


def is_noise(post: dict) -> bool:
    """Return True if the post should be filtered out as noise."""
    text = (post.get("title", "") + " " + post.get("selftext", "")).lower()
    return any(kw in text for kw in NOISE_KEYWORDS)


def filter_posts(posts: list, min_score: int, max_age_days: int) -> list:
    """Filter posts by score, age, noise keywords, stickied status."""
    cutoff = time.time() - (max_age_days * 86400)
    out = []

    for p in posts:
        if p.get("stickied"):
            continue
        if p.get("score", 0) < min_score:
            continue
        if p.get("created_utc", 0) < cutoff:
            continue
        if is_noise(p):
            continue

        out.append({
            "title": p.get("title", ""),
            "score": p.get("score", 0),
            "subreddit": p.get("subreddit", ""),
            "url": p.get("url", ""),
            "permalink": "https://www.reddit.com" + p.get("permalink", ""),
            "created_utc": p.get("created_utc", 0),
            "selftext_preview": p.get("selftext", "")[:300],
            "num_comments": p.get("num_comments", 0),
        })

    # Sort by score descending — highest-signal first
    out.sort(key=lambda x: x["score"], reverse=True)
    return out


def main():
    parser = argparse.ArgumentParser(description="Fetch and filter Reddit posts.")
    parser.add_argument("subreddits", nargs="+", help="Subreddits (e.g., r/tampa)")
    parser.add_argument("--min-score", type=int, default=30,
                        help="Minimum post score (default 30)")
    parser.add_argument("--days", type=int, default=14,
                        help="Maximum post age in days (default 14)")
    parser.add_argument("--limit", type=int, default=50,
                        help="Posts per subreddit to fetch (default 50, max 100)")
    args = parser.parse_args()

    all_posts = []
    for sub in args.subreddits:
        raw = fetch_subreddit(sub, limit=args.limit)
        filtered = filter_posts(raw, min_score=args.min_score, max_age_days=args.days)
        print(
            f"{sub}: fetched {len(raw)}, kept {len(filtered)} after filtering",
            file=sys.stderr,
        )
        all_posts.extend(filtered)
        # Be polite to Reddit — small delay between requests
        time.sleep(0.5)

    # Re-sort across subreddits by score
    all_posts.sort(key=lambda x: x["score"], reverse=True)
    print(json.dumps(all_posts, indent=2))


if __name__ == "__main__":
    main()
