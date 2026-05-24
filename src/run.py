"""End-to-end orchestrator: fetch -> filter -> dedup -> rank -> summarize -> render."""
from __future__ import annotations

import argparse
import logging
import os
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from anthropic import Anthropic
from google.cloud import bigquery

from src.dedup import Cluster, cluster
from src.fetch import fetch
from src.filter import filter_and_tag
from src.render import render
from src.summarize import write_intro

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("run")
MADRID = ZoneInfo("Europe/Madrid")


def _madrid_yesterday() -> date:
    return (datetime.now(MADRID) - timedelta(days=1)).date()


LONGTAIL_MIN_CLUSTER_SIZE = 2
LONGTAIL_MAX_ITEMS = 50


def _rank(clusters: list[Cluster]) -> list[Cluster]:
    """Within-tier: cluster size desc, then canonical recency desc."""
    return sorted(
        clusters,
        key=lambda c: (-c.size, -c.canonical.article.date.timestamp()),
    )


def _trim_longtail(clusters: list[Cluster]) -> list[Cluster]:
    """Drop singletons and cap to top N — the page stays readable."""
    filtered = [c for c in clusters if c.size >= LONGTAIL_MIN_CLUSTER_SIZE]
    return filtered[:LONGTAIL_MAX_ITEMS]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--date",
        type=lambda s: date.fromisoformat(s),
        default=None,
        help="Madrid local day (YYYY-MM-DD). Default: yesterday Madrid time.",
    )
    p.add_argument(
        "--no-llm",
        action="store_true",
        help="Skip Claude intro and use a placeholder line.",
    )
    args = p.parse_args()
    day = args.date or _madrid_yesterday()
    log.info("Building digest for Madrid day %s", day)

    bq = bigquery.Client()
    articles = fetch(bq, day)
    tagged = filter_and_tag(articles)
    clusters = cluster(tagged)

    whitelist = _rank([c for c in clusters if c.canonical.tier == "whitelist"])
    longtail = _trim_longtail(_rank([c for c in clusters if c.canonical.tier == "longtail"]))

    if args.no_llm or not os.environ.get("ANTHROPIC_API_KEY"):
        intro = f"{len(whitelist)} tier-1 stories, {len(longtail)} long-tail."
    else:
        intro = write_intro(Anthropic(), day, whitelist[:10])

    out = render(day, intro, whitelist, longtail)
    log.info("Done: %s", out)


if __name__ == "__main__":
    main()
