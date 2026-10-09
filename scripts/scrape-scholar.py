#!/usr/bin/env python3
"""Fetch Google Scholar profile works into مقالات-علمی/data/index.json."""

from __future__ import annotations

import html
import json
import re
import time
import unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "مقالات-علمی" / "data" / "index.json"
SCHOLAR_USER = "13wD0fwAAAAJ"
SCHOLAR_URL = f"https://scholar.google.com/citations?user={SCHOLAR_USER}&hl=en"
PAGE_SIZE = 100
DELAY_SEC = 2.5

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

TOPIC_RULES: list[tuple[str, str]] = [
    (r"sinus|rhinosinusitis|fess|endoscopic sinus|nasal polyp|sphenoid|ethmoid", "سینوس"),
    (r"rhinoplast|septorhinoplast|septoplasty|nasal deform|nose job|aesthetic nose", "رینوپلاستی"),
    (r"skull base|pituitary|cranial base|jugu|clival|petrous|transsphenoidal", "قاعده جمجمه"),
    (r"rhinology|nasal cavity|olfactory|turbinat|epistaxis|nosebleed", "راینولوژی"),
    (r"otolog|cochlear|tympan|mastoid|ear surgery|hearing|stapes|cholesteatoma", "گوش"),
    (r"laryng|pharyn|tonsil|voice|thyroid|parotid|salivary|neck dissection|head and neck", "گلو و حلق"),
    (r"endoscop|fess|sinus surgery", "آندوسکوپی"),
    (r"allerg|asthma|immunolog", "آلرژی و ایمونولوژی"),
    (r"pediatric|child|children|infant", "اطفال"),
    (r"sleep apnea|osa|snor", "اختلالات خواب"),
]


def slugify(text: str, max_len: int = 48) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:max_len] or "paper"


def guess_topic(title: str, journal: str) -> str:
    hay = f"{title} {journal}".lower()
    for pattern, topic in TOPIC_RULES:
        if re.search(pattern, hay, re.I):
            return topic
    return "تحقیقاتی"


def strip_tags(fragment: str) -> str:
    text = re.sub(r"<[^>]+>", " ", fragment)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def parse_work_rows(page_html: str) -> list[dict]:
    rows: list[dict] = []
    for block in re.findall(r'<tr class="gsc_a_tr">(.*?)</tr>', page_html, re.S):
        title_m = re.search(
            r'<a\s+[^>]*class="gsc_a_at"[^>]*>(.*?)</a>', block, re.S
        )
        if not title_m:
            continue
        tag_m = re.search(r"<a\s+([^>]*class=\"gsc_a_at\"[^>]*)>", block, re.S)
        href_m = re.search(r'href="([^"]+)"', tag_m.group(1) if tag_m else block)
        href = html.unescape(href_m.group(1) if href_m else "")
        title_raw = title_m.group(1)
        title = strip_tags(title_raw)
        grays = [strip_tags(g) for g in re.findall(r'<div class="gs_gray">(.*?)</div>', block, re.S)]
        authors = grays[0] if grays else ""
        journal = grays[1] if len(grays) > 1 else ""
        journal = re.sub(r",\s*\d{4}\s*$", "", journal).strip()
        year_m = re.search(r'class="gsc_a_y"[^>]*>.*?(\d{4})', block, re.S)
        year = int(year_m.group(1)) if year_m else None
        if year is None and grays:
            oph = re.search(r",\s*(\d{4})\s*$", grays[-1])
            if oph:
                year = int(oph.group(1))
        cite_m = re.search(r'class="gsc_a_ac[^"]*"[^>]*>\s*(\d*)\s*<', block)
        citations = int(cite_m.group(1)) if cite_m and cite_m.group(1) else 0
        url = href if href.startswith("http") else "https://scholar.google.com" + href
        rows.append(
            {
                "title": title,
                "authors": authors,
                "journal": journal,
                "year": year,
                "citations": citations,
                "url": normalize_citation_url(url),
            }
        )
    return rows


def normalize_citation_url(url: str) -> str:
    if not url:
        return SCHOLAR_URL
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    cite = (qs.get("citation_for_view") or [None])[0]
    if cite:
        return (
            f"https://scholar.google.com/citations?view_op=view_citation&hl=en"
            f"&user={SCHOLAR_USER}&citation_for_view={cite}"
        )
    return url


def fetch(url: str) -> str:
    req = Request(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    with urlopen(req, timeout=60) as resp:
        raw = resp.read()
    return raw.decode("utf-8", errors="replace")


def parse_stats(html: str) -> dict:
    nums = [int(x) for x in re.findall(r'class="gsc_rsb_std">(\d+)<', html)]
    return {
        "citations": nums[0] if nums else 0,
        "hIndex": nums[2] if len(nums) > 2 else 0,
        "i10Index": nums[4] if len(nums) > 4 else 0,
    }


def fetch_all_works() -> tuple[list[dict], dict]:
    all_rows: list[dict] = []
    stats = {"citations": 0, "hIndex": 0, "i10Index": 0}
    cstart = 0
    first = True
    while True:
        url = (
            f"https://scholar.google.com/citations?hl=en&user={SCHOLAR_USER}"
            f"&view_op=list_works&sortby=pubdate&cstart={cstart}&pagesize={PAGE_SIZE}"
        )
        html = fetch(url)
        if first:
            stats = parse_stats(html)
            first = False
        if "sorry" in html.lower() and "captcha" in html.lower():
            raise RuntimeError("Google Scholar CAPTCHA — run scrape-scholar.py locally in a browser session.")
        batch = parse_work_rows(html)
        if not batch:
            break
        all_rows.extend(batch)
        if len(batch) < PAGE_SIZE:
            break
        cstart += PAGE_SIZE
        time.sleep(DELAY_SEC)
    return all_rows, stats


def dedupe(rows: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for r in rows:
        key = re.sub(r"\s+", " ", r["title"].lower().strip())
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def build_publications(rows: list[dict]) -> list[dict]:
    pubs = []
    for i, r in enumerate(rows):
        year = r.get("year") or 0
        title = r["title"]
        pid = f"{year}-{slugify(title)}-{i}"
        pubs.append(
            {
                "id": pid,
                "title": title,
                "authors": r.get("authors") or "",
                "journal": r.get("journal") or "",
                "year": year,
                "citations": int(r.get("citations") or 0),
                "topic": guess_topic(title, r.get("journal") or ""),
                "url": r.get("url") or SCHOLAR_URL,
            }
        )
    pubs.sort(key=lambda p: (-(p["year"] or 0), -p["citations"]))
    return pubs


def main() -> None:
    rows, stats = fetch_all_works()
    rows = dedupe(rows)
    publications = build_publications(rows)
    stats["total"] = len(publications)
    stats["scholarUrl"] = SCHOLAR_URL
    payload = {
        "updated": date.today().isoformat(),
        "stats": stats,
        "publications": publications,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(publications)} publications")
    print(f"Stats: citations={stats['citations']} h={stats['hIndex']} i10={stats['i10Index']}")


if __name__ == "__main__":
    main()
