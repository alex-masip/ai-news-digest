"""Claude Haiku 3-sentence digest intro."""
from __future__ import annotations

import logging
from datetime import date

from anthropic import Anthropic

from src.dedup import Cluster

log = logging.getLogger(__name__)
MODEL = "claude-haiku-4-5-20251001"

SYSTEM = """You write a 3-sentence intro for a personal daily AI-news digest.

Style:
- Exactly 3 sentences, ~60 words total.
- Lead with the single most important story. Cover up to 2 more.
- Neutral, informative voice. No hype words ("revolutionary", "game-changer", "breakthrough").
- Refer to companies and products by name. Do not cite outlets.
- Do not introduce yourself, the digest, or the date. No headers, no markdown.
"""


def write_intro(client: Anthropic, day: date, top_clusters: list[Cluster]) -> str:
    if not top_clusters:
        return "No notable AI stories cleared the filter for this day."

    lines: list[str] = []
    for i, c in enumerate(top_clusters, 1):
        a = c.canonical.article
        line = f"{i}. ({c.size}x outlets) {a.outlet}: {a.title}"
        if a.desc:
            line += f" — {a.desc[:240]}"
        lines.append(line)

    user_msg = (
        f"AI news for {day.isoformat()}. Top clusters, ranked by number of outlets covering them:\n\n"
        + "\n".join(lines)
    )

    resp = client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=SYSTEM,
        messages=[{"role": "user", "content": user_msg}],
    )
    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    log.info("Intro: %d chars", len(text))
    return text
