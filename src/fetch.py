"""Fetch AI articles from gdelt-bq.gdeltv2.gal for a Madrid-local day."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from google.cloud import bigquery

from src.config import bq_positive_regex

log = logging.getLogger(__name__)
MADRID = ZoneInfo("Europe/Madrid")
UTC = ZoneInfo("UTC")


@dataclass
class Article:
    date: datetime  # UTC, from GAL
    url: str
    domain: str
    outlet: str
    title: str
    desc: str | None
    image: str | None
    author: str | None


def madrid_day_utc_window(target: date) -> tuple[datetime, datetime]:
    """[start_utc, end_utc) covering the Madrid-local day `target`."""
    start_madrid = datetime.combine(target, time.min, tzinfo=MADRID)
    end_madrid = start_madrid + timedelta(days=1)
    return start_madrid.astimezone(UTC), end_madrid.astimezone(UTC)


def fetch(client: bigquery.Client, target_date: date) -> list[Article]:
    start_utc, end_utc = madrid_day_utc_window(target_date)
    log.info(
        "Fetching GAL rows for Madrid %s (UTC %s -> %s)",
        target_date, start_utc.isoformat(), end_utc.isoformat(),
    )

    query = """
    SELECT
      date, url, domain, outletName AS outlet, title,
      `desc` AS desc_text, image, author
    FROM `gdelt-bq.gdeltv2.gal`
    WHERE date >= @start_ts
      AND date < @end_ts
      AND lang = 'en'
      AND title IS NOT NULL
      AND REGEXP_CONTAINS(LOWER(title), @ai_regex)
    """
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("start_ts", "TIMESTAMP", start_utc),
            bigquery.ScalarQueryParameter("end_ts", "TIMESTAMP", end_utc),
            bigquery.ScalarQueryParameter("ai_regex", "STRING", bq_positive_regex()),
        ],
    )
    rows = list(client.query(query, job_config=job_config).result())
    log.info("GAL returned %d rows", len(rows))

    return [
        Article(
            date=r.date,
            url=r.url,
            domain=r.domain,
            outlet=r.outlet or r.domain,
            title=r.title,
            desc=r.desc_text,
            image=r.image,
            author=r.author,
        )
        for r in rows
    ]
