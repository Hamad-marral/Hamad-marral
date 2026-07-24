#!/usr/bin/env python3
"""
Pulls the public contribution calendar for a GitHub user without any token,
by scraping the same HTML fragment the profile page itself renders.

Writes: assets/contributions.json
"""
import json
import os
import sys
from datetime import datetime
from collections import Counter

import httpx
from lxml import html

USERNAME = os.environ.get("GH_USERNAME", "Hamad-marral")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "contributions.json")


def fetch_calendar(username: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (living-terminal-readme-bot)"}
    with httpx.Client(timeout=20, headers=headers, follow_redirects=True) as client:
        resp = client.get(f"https://github.com/users/{username}/contributions")
        resp.raise_for_status()
        return resp.text


def parse_days(page_html: str):
    tree = html.fromstring(page_html)
    # GitHub renders each day as a <td> with class "ContributionCalendar-day"
    # and data-date / data-level attributes. The human-readable count lives
    # in a separate <tool-tip> element, matched by id <-> aria-describedby.
    tooltip_text_by_cell_id = {}
    for tip in tree.xpath('//tool-tip[@for]'):
        cell_id = tip.get("for")
        tooltip_text_by_cell_id[cell_id] = "".join(tip.itertext()).strip()

    cells = tree.xpath('//td[contains(@class,"ContributionCalendar-day")]')
    days = []
    for cell in cells:
        date_str = cell.get("data-date")
        level = cell.get("data-level")
        if date_str is None:
            continue
        count = 0
        cell_id = cell.get("id")
        tooltip = tooltip_text_by_cell_id.get(cell_id, "") if cell_id else ""
        if tooltip:
            first_token = tooltip.split()[0].replace(",", "")
            if first_token.lower() == "no":
                count = 0
            else:
                try:
                    count = int(first_token)
                except ValueError:
                    count = 0
        days.append({
            "date": date_str,
            "level": int(level) if level is not None else 0,
            "count": count,
        })
    days.sort(key=lambda d: d["date"])
    return days


def compute_stats(days):
    total = sum(d["count"] for d in days)
    # current streak (counting back from the most recent day with data)
    current_streak = 0
    for d in reversed(days):
        if d["count"] > 0:
            current_streak += 1
        else:
            break
    # longest streak
    longest_streak = 0
    running = 0
    for d in days:
        if d["count"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0
    # busiest weekday
    weekday_counts = Counter()
    for d in days:
        dt = datetime.strptime(d["date"], "%Y-%m-%d")
        weekday_counts[dt.strftime("%A")] += d["count"]
    busiest_day = max(weekday_counts, key=weekday_counts.get) if weekday_counts else None
    return {
        "total": total,
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "busiest_day": busiest_day,
    }


def main():
    try:
        page_html = fetch_calendar(USERNAME)
        days = parse_days(page_html)
    except Exception as e:
        print(f"warning: live fetch failed ({e}); writing empty calendar", file=sys.stderr)
        days = []

    stats = compute_stats(days) if days else {
        "total": 0, "current_streak": 0, "longest_streak": 0, "busiest_day": None
    }

    out = {"username": USERNAME, "days": days, "stats": stats}
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {len(days)} days -> {OUT_PATH}")


if __name__ == "__main__":
    main()
