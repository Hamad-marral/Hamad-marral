#!/usr/bin/env python3
"""
Draws a small terminal "system info" panel that appears to type itself out,
row by row. Set PREVIEW=1 to render a still frame (all rows visible, no
animation) for quick checking in a normal image viewer.

Writes: sysinfo.svg
"""
import os
from xml.sax.saxutils import escape

OUT = os.path.join(os.path.dirname(__file__), "..", "sysinfo.svg")

BG = "#0d0d17"
BORDER = "#1c7ed6"
LABEL = "#5c6b8a"
VALUE = "#a5d8ff"
ACCENT = "#4dabf7"

# Edit these to describe yourself — this is the only part of the whole
# project that has to be written by hand.
ROWS = [
    ("role", "AI Automation Engineer"),
    ("focus", "AI Agents | LLMs | Workflow Automation | Intelligent Systems | Chatbots"),
    ("stack", "Python | OpenAI | LangChain | MCP | FastAPI | n8n | PostgreSQL | Docker"),
    ("now", "Building AI Systems That Think, Reason & Automate"),
]

WIDTH = 460
LINE_H = 18          # height of a single wrapped line
ROW_GAP = 16         # extra breathing room after a row's last line
PAD_TOP = 54
PAD_X = 24
VALUE_X = PAD_X + 100
HEADER_H = 40
FONT_SIZE = 14
CHAR_W = FONT_SIZE * 0.6           # approx monospace advance width
VALUE_MAX_CHARS = max(8, int((WIDTH - VALUE_X - PAD_X) / CHAR_W))

PREVIEW = os.environ.get("PREVIEW") == "1"


def wrap_value(value: str, max_chars: int):
    """Greedy word-wrap; falls back to a hard break for single long tokens."""
    words = value.split(" ")
    lines, current = [], ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            # hard-break a single word that's longer than the whole line
            while len(word) > max_chars:
                lines.append(word[:max_chars])
                word = word[max_chars:]
            current = word
    if current:
        lines.append(current)
    return lines or [""]


def render():
    wrapped_rows = [(label, wrap_value(value, VALUE_MAX_CHARS)) for label, value in ROWS]
    row_heights = [len(lines) * LINE_H + ROW_GAP for _, lines in wrapped_rows]
    height = PAD_TOP - LINE_H + sum(row_heights) + 20

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" font-family="Menlo, Consolas, monospace">'
    )
    parts.append(
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="10" '
        f'fill="{BG}" stroke="{BORDER}" stroke-width="1"/>'
    )
    # header bar with three dots, like a terminal chrome
    parts.append(f'<rect x="0" y="0" width="{WIDTH}" height="{HEADER_H}" rx="10" fill="{BORDER}" opacity="0.12"/>')
    for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        parts.append(f'<circle cx="{20 + i * 18}" cy="{HEADER_H / 2}" r="5" fill="{c}"/>')
    parts.append(
        f'<text x="{WIDTH - PAD_X}" y="{HEADER_H / 2 + 4}" text-anchor="end" '
        f'fill="{LABEL}" font-size="12">whoami --verbose</text>'
    )

    delay_step = 0.35
    y = PAD_TOP
    for i, (label, lines) in enumerate(wrapped_rows):
        row_delay = i * delay_step
        opacity_attrs = "" if PREVIEW else (
            f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{row_delay:.2f}s" dur="0.4s" fill="freeze"/>'
        )
        start_opacity = "1" if PREVIEW else "0"
        parts.append(f'<g opacity="{start_opacity}">{opacity_attrs}' if not PREVIEW else '<g>')
        parts.append(
            f'<text x="{PAD_X}" y="{y}" fill="{ACCENT}" font-size="{FONT_SIZE}">&gt;</text>'
        )
        parts.append(
            f'<text x="{PAD_X + 16}" y="{y}" fill="{LABEL}" font-size="{FONT_SIZE}">{escape(label)}</text>'
        )
        for li, line in enumerate(lines):
            parts.append(
                f'<text x="{VALUE_X}" y="{y + li * LINE_H}" fill="{VALUE}" '
                f'font-size="{FONT_SIZE}">{escape(line)}</text>'
            )
        parts.append('</g>')
        y += len(lines) * LINE_H + ROW_GAP

    parts.append('</svg>')
    return "\n".join(parts)


def main():
    svg = render()
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
