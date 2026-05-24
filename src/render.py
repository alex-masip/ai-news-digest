"""Render clusters + intro to HTML and JSON."""
from __future__ import annotations

import json
import logging
import shutil
from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.dedup import Cluster

log = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent
PUBLIC = ROOT / "public"
DATA = ROOT / "data"
TEMPLATES = ROOT / "templates"


def _cluster_to_dict(c: Cluster) -> dict:
    a = c.canonical.article
    return {
        "title": a.title,
        "url": a.url,
        "domain": a.domain,
        "outlet": a.outlet,
        "image": a.image,
        "desc": a.desc,
        "date": a.date.isoformat(),
        "tier": c.canonical.tier,
        "cluster_size": c.size,
        "other_outlets": sorted(
            {m.article.outlet for m in c.members if m.article.outlet != a.outlet}
        )[:6],
    }


def render(
    day: date,
    intro: str,
    whitelist_clusters: list[Cluster],
    longtail_clusters: list[Cluster],
) -> Path:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("day.html.j2")

    wl = [_cluster_to_dict(c) for c in whitelist_clusters]
    lt = [_cluster_to_dict(c) for c in longtail_clusters]

    html = template.render(day=day.isoformat(), intro=intro, whitelist=wl, longtail=lt)

    PUBLIC.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    out_html = PUBLIC / f"{day.isoformat()}.html"
    out_html.write_text(html)
    shutil.copyfile(out_html, PUBLIC / "index.html")

    out_json = DATA / f"{day.isoformat()}.json"
    out_json.write_text(
        json.dumps(
            {"date": day.isoformat(), "intro": intro, "whitelist": wl, "longtail": lt},
            indent=2,
            ensure_ascii=False,
        )
    )

    log.info("Wrote %s (%d whitelist, %d longtail)", out_html, len(wl), len(lt))
    return out_html
