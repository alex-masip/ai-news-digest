"""Cluster near-duplicate articles by fuzzy title match."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from rapidfuzz import fuzz

from src.filter import TaggedArticle

log = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 85
_NORMALIZE_RE = re.compile(r"[^a-z0-9 ]+")
_WS_RE = re.compile(r"\s+")
# Strip common outlet-name suffix delimiters: " | Outlet", " - Outlet", " · Outlet"
_SUFFIX_RE = re.compile(r"\s*[|\-·–—]\s*[^|\-·–—]{1,40}$")


def _normalize(title: str) -> str:
    t = (title or "").lower()
    t = _SUFFIX_RE.sub("", t)
    t = _NORMALIZE_RE.sub(" ", t)
    return _WS_RE.sub(" ", t).strip()


@dataclass
class Cluster:
    canonical: TaggedArticle
    members: list[TaggedArticle]

    @property
    def size(self) -> int:
        return len(self.members)


def _better_canonical(a: TaggedArticle, b: TaggedArticle) -> TaggedArticle:
    """Whitelist > more recent > shorter URL."""
    if a.tier != b.tier:
        return a if a.tier == "whitelist" else b
    if a.article.date != b.article.date:
        return a if a.article.date > b.article.date else b
    return a if len(a.article.url) <= len(b.article.url) else b


def cluster(tagged: list[TaggedArticle]) -> list[Cluster]:
    """Greedy clustering — compare each article to existing cluster canonicals."""
    clusters: list[Cluster] = []
    canonical_norms: list[str] = []

    for art in tagged:
        norm = _normalize(art.article.title)
        if not norm:
            continue
        matched = -1
        for j, other_norm in enumerate(canonical_norms):
            if fuzz.token_set_ratio(norm, other_norm) >= SIMILARITY_THRESHOLD:
                matched = j
                break
        if matched == -1:
            clusters.append(Cluster(canonical=art, members=[art]))
            canonical_norms.append(norm)
        else:
            c = clusters[matched]
            c.members.append(art)
            new_canonical = _better_canonical(c.canonical, art)
            if new_canonical is not c.canonical:
                c.canonical = new_canonical
                canonical_norms[matched] = _normalize(new_canonical.article.title)
    log.info("Dedup: %d articles -> %d clusters", len(tagged), len(clusters))
    return clusters
