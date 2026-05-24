"""Apply blocklist + negative-pattern + tier tagging to fetched articles."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Literal

from src.config import BLOCKLIST, NEGATIVE_REGEX, WHITELIST
from src.fetch import Article

log = logging.getLogger(__name__)

Tier = Literal["whitelist", "longtail"]


@dataclass
class TaggedArticle:
    article: Article
    tier: Tier


def filter_and_tag(articles: list[Article]) -> list[TaggedArticle]:
    out: list[TaggedArticle] = []
    dropped_block = 0
    dropped_neg = 0
    for art in articles:
        if art.domain in BLOCKLIST:
            dropped_block += 1
            continue
        haystack = f"{(art.title or '').lower()} {(art.desc or '').lower()}"
        if NEGATIVE_REGEX.search(haystack):
            dropped_neg += 1
            continue
        tier: Tier = "whitelist" if art.domain in WHITELIST else "longtail"
        out.append(TaggedArticle(article=art, tier=tier))
    log.info(
        "Filter: kept %d / %d (dropped %d blocklist, %d negative)",
        len(out), len(articles), dropped_block, dropped_neg,
    )
    return out
