#!/usr/bin/env python3
"""
Draws assets/contributions.json as a 52-ish-week x 7-day grid of rounded
squares, animated in column by column, with a small legend and stats line.

Writes: graph.svg
"""
import json
import os
from datetime import datetime, timedelta

ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets", "contributions.json")
OUT = os.path.join(os.path.dirname(__file__), "..", "graph.svg")

LEVELS = ["#1a1a2e", "#16537e", "#1c7ed6", "#4dabf7", "#a5d8ff"]
BG = "#0d0d17"
TEXT = "#a5d8ff"
DIM = "#5c6b8a"

CELL = 11
GAP = 3
LEFT_PAD = 30
TOP_PAD = 30
LEGEND_H = 24
STATS_H = 26


def load_data():
    with open(ASSETS) as f:
        return json.load(f)


def weeks_from_days(days):
    """Bucket days into GitHub-style week columns starting on Sunday."""
    by_date = {d["date"]: d for d in days}
    if not days:
        return []
    start = datetime.strptime(days[0]["date"], "%Y-%m-%d")
    # walk back to the preceding Sunday so columns line up
    start -= timedelta(days=(start.weekday() + 1) % 7)
    end = datetime.strptime(days[-1]["date"], "%Y-%m-%d")

    weeks = []
    cur = start
    week = []
    while cur <= end:
        key = cur.strftime("%Y-%m-%d")
        cell = by_date.get(key, {"date": key, "level": 0, "count": 0})
        week.append(cell)
        if len(week) == 7:
            weeks.append(week)
            week = []
        cur += timedelta(days=1)
    if week:
        while len(week) < 7:
            week.append({"date": None, "level": 0, "count": 0})
        weeks.append(week)
    return weeks


def render(data):
    days = data["days"]
    stats = data["stats"]
    weeks = weeks_from_days(days)
    n_weeks = len(weeks)

    width = LEFT_PAD * 2 + n_weeks * (CELL + GAP)
    height = TOP_PAD + 7 * (CELL + GAP) + LEGEND_H + STATS_H + 20

    svg_parts = []
    svg_parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="Menlo, Consolas, monospace">'
    )
    svg_parts.append(f'<rect width="100%" height="100%" fill="{BG}" rx="10"/>')

    # animate column by column (each week = one column)
    col_delay_step = 0.045
    for wi, week in enumerate(weeks):
        col_delay = wi * col_delay_step
        for di, day in enumerate(week):
            x = LEFT_PAD + wi * (CELL + GAP)
            y = TOP_PAD + di * (CELL + GAP)
            level = day.get("level", 0) if day.get("date") else 0
            color = LEVELS[min(level, len(LEVELS) - 1)]
            svg_parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" '
                f'fill="{color}" opacity="0">'
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{col_delay:.3f}s" dur="0.25s" fill="freeze"/>'
                f'</rect>'
            )

    # legend
    legend_y = TOP_PAD + 7 * (CELL + GAP) + 14
    svg_parts.append(
        f'<text x="{LEFT_PAD}" y="{legend_y + 9}" fill="{DIM}" font-size="11">less</text>'
    )
    lx = LEFT_PAD + 34
    for i, color in enumerate(LEVELS):
        svg_parts.append(
            f'<rect x="{lx + i * (CELL + GAP)}" y="{legend_y}" width="{CELL}" height="{CELL}" '
            f'rx="2" fill="{color}"/>'
        )
    lx_end = lx + len(LEVELS) * (CELL + GAP) + 6
    svg_parts.append(
        f'<text x="{lx_end}" y="{legend_y + 9}" fill="{DIM}" font-size="11">more</text>'
    )

    # stats line
    stats_y = legend_y + LEGEND_H
    busiest = stats.get("busiest_day") or "—"
    stats_text = (
        f'{stats.get("total", 0)} contributions this year &middot; '
        f'current streak {stats.get("current_streak", 0)}d &middot; '
        f'longest {stats.get("longest_streak", 0)}d &middot; '
        f'busiest day {busiest}'
    )
    svg_parts.append(
        f'<text x="{LEFT_PAD}" y="{stats_y}" fill="{TEXT}" font-size="12">{stats_text}</text>'
    )

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def main():
    data = load_data()
    svg = render(data)
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
