"""
Daily verse sources.

Where verses come from (in order):
  1. A DailyVerse row already saved for that date (seeded sample month, an
     earlier fetch, or one you typed into the admin).
  2. An online "verse of the day" feed, picked by settings.DAILY_VERSE_SOURCE:
       - "ourmanna": OurManna's daily verse  (https://beta.ourmanna.com/api/v1/)
       - "netbible": Bible.org NET Bible VOTD (https://labs.bible.org/api/?passage=votd)
     Only the *reference* is taken from the feed; the text is then pulled in the
     public-domain World English Bible from bible-api.com, so the stored text
     carries no licensing strings. If that lookup fails, the feed's own text is kept.
  3. The bundled 31-day sample (journal/data/daily_verses_sample.json), by day of month.
"""
import json
import logging
from datetime import date
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

import requests
from django.conf import settings

from .models import DailyVerse

log = logging.getLogger(__name__)

SAMPLE_PATH = Path(__file__).resolve().parent / "data" / "daily_verses_sample.json"
TIMEOUT = 10
HEADERS = {"User-Agent": "bible-journal/1.0"}


@lru_cache(maxsize=1)
def sample_verses():
    with open(SAMPLE_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def sample_for(day: date) -> dict:
    verses = sample_verses()
    v = verses[(day.day - 1) % len(verses)]
    return {"reference": v["reference"], "text": v["text"],
            "translation": v.get("translation", "WEB"), "source": "sample"}


# ── Online feeds ─────────────────────────────────────────────────────────────

def fetch_web_text(reference: str):
    """Public-domain World English Bible text for a reference, via bible-api.com."""
    r = requests.get(f"https://bible-api.com/{quote(reference)}",
                     params={"translation": "web"}, timeout=TIMEOUT, headers=HEADERS)
    r.raise_for_status()
    d = r.json()
    text = " ".join(v["text"].strip() for v in d.get("verses", []))
    return d.get("reference", reference), " ".join(text.split())


def fetch_ourmanna():
    r = requests.get("https://beta.ourmanna.com/api/v1/get",
                     params={"format": "json", "order": "daily"}, timeout=TIMEOUT, headers=HEADERS)
    r.raise_for_status()
    det = r.json()["verse"]["details"]
    return {"reference": det["reference"], "text": det["text"],
            "translation": det.get("version", "NIV"), "source": "ourmanna"}


def fetch_netbible():
    r = requests.get("https://labs.bible.org/api/",
                     params={"passage": "votd", "type": "json"}, timeout=TIMEOUT, headers=HEADERS)
    r.raise_for_status()
    rows = r.json()
    first, last = rows[0], rows[-1]
    ref = f'{first["bookname"]} {first["chapter"]}:{first["verse"]}'
    if len(rows) > 1:
        ref += f'-{last["verse"]}' if last["chapter"] == first["chapter"] else f'-{last["chapter"]}:{last["verse"]}'
    text = " ".join(x["text"].strip() for x in rows)
    return {"reference": ref, "text": " ".join(text.split()),
            "translation": "NET", "source": "netbible"}


FEEDS = {"ourmanna": fetch_ourmanna, "netbible": fetch_netbible}


def fetch_online(source: str):
    """Today's verse from an online feed, with the text swapped to WEB when possible."""
    verse = FEEDS[source]()
    try:
        ref, text = fetch_web_text(verse["reference"])
        if text:
            verse.update(reference=ref, text=text, translation="WEB")
    except Exception as exc:  # keep the feed's own text
        log.warning("WEB lookup failed for %s: %s", verse["reference"], exc)
    return verse


# ── Public API ───────────────────────────────────────────────────────────────

def verse_for(day: date, allow_fetch: bool = False) -> dict:
    """
    The verse for `day`. With allow_fetch=True (used by the scheduled command)
    a missing day is fetched online and saved; page views never wait on the network.
    """
    row = DailyVerse.objects.filter(date=day).first()
    if row:
        return {"reference": row.reference, "text": row.text,
                "translation": row.translation, "source": row.source}

    source = getattr(settings, "DAILY_VERSE_SOURCE", "ourmanna")
    if allow_fetch and source in FEEDS and day == date.today():
        try:
            verse = fetch_online(source)
            DailyVerse.objects.update_or_create(date=day, defaults=verse)
            return verse
        except Exception as exc:
            log.warning("Daily verse feed %s failed: %s", source, exc)

    verse = sample_for(day)
    if allow_fetch:
        DailyVerse.objects.update_or_create(date=day, defaults=verse)
    return verse
