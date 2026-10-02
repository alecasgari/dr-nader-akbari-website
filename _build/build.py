"""Static article builder for drnaderakbari.com.

  python _build/build.py                       build everything
  python _build/build.py new <slug> "<title>" [--pillar <slug>] [--type pillar]
  python _build/build.py publish <slug>
  python _build/build.py list
"""

import datetime as dt
import html
import json
import math
import re
import secrets
import sys
from pathlib import Path
from urllib.parse import quote

import markdown
import yaml
from markdown.extensions.toc import slugify_unicode

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "_build"
CONTENT = ROOT / "_content"
TEMPLATES = BUILD / "templates"
MANIFEST = BUILD / "manifest.json"

SITE = "https://drnaderakbari.com"
DOCTOR_ID = SITE + "/#doctor"
DOCTOR = "دکتر نادر اکبری دیلمقانی"
ENDPOINT = "https://n8n.alecasgari.com/webhook/dr-akbari-approval"
DRAFT_DIR = "پیش-نویس"
HUB_DIR = "مقالات"
DEFAULT_IMAGE = SITE + "/images/hero.webp"
STATIC_PAGES = [("/", "1.0"), ("/دستورالعمل/", "0.8")]

ANALYTICS = """  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){ dataLayer.push(arguments); }
    gtag("js", new Date());
    gtag("config", "GT-TNF2V7K");
    gtag("config", "G-T3P18C5N3Q");
    addEventListener("load", function () {
      setTimeout(function () {
        var s = document.createElement("script");
        s.async = true;
        s.src = "https://www.googletagmanager.com/gtag/js?id=GT-TNF2V7K";
        document.head.appendChild(s);
      }, 1500);
    });
  </script>"""

FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
FA_MONTHS = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
             "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]


def fa(n):
    return str(n).translate(FA_DIGITS)


def g2j(d):
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    gy, gm, gd = d.year, d.month, d.day
    gy2 = gy + 1 if gm > 2 else gy
    days = (355666 + 365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100
            + (gy2 + 399) // 400 + gd + g_d_m[gm - 1])
    jy = -1595 + 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm, jd = 1 + days // 31, 1 + days % 31
    else:
        jm, jd = 7 + (days - 186) // 30, 1 + (days - 186) % 30
    return jy, jm, jd


def jalali(d):
    jy, jm, jd = g2j(d)
    return f"{fa(jd)} {FA_MONTHS[jm - 1]} {fa(jy)}"


def as_date(v):
    if not v:
        return None
    if isinstance(v, dt.date):
        return v
    return dt.date.fromisoformat(str(v))


def esc(s):
    return html.escape(str(s or ""), quote=True)


def url_path(slug):
    return "/" + slug + "/"


def abs_url(path):
    return SITE + quote(path)


def fill(tpl, **kw):
    return re.sub(r"{{(\w+)}}", lambda m: str(kw.get(m.group(1), "")), tpl)


def tpl(name):
    return (TEMPLATES / name).read_text(encoding="utf-8")


def wa_path():
    src = (ROOT / "دستورالعمل" / "index.html").read_text(encoding="utf-8")
    return re.search(r'class="wa-ico"[^>]*><path d="([^"]+)"', src).group(1)


def json_ld(data):
    s = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return '  <script type="application/ld+json">\n  ' + s.replace("</", "<\\/") + "\n  </script>"


# ---------- content ----------

class Page:
    def __init__(self, path):
        self.file = path
        raw = path.read_text(encoding="utf-8").replace("\r\n", "\n")
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
        if not m:
            raise SystemExit(f"{path.name}: front matter missing")
        self.meta = yaml.safe_load(m.group(1)) or {}
        self.source = m.group(2).strip()
        g = self.meta.get
        self.slug = str(g("slug") or path.stem).strip("/")
        self.title = g("title") or self.slug
        self.type = g("type", "article")
        self.pillar = str(g("pillar") or "").strip("/")
        self.status = g("status", "draft")
        self.token = g("token")
        self.published = as_date(g("published"))
        self.updated = as_date(g("updated")) or self.published
        self.reviewed = as_date(g("reviewed")) or self.updated
        self.description = g("description", "")

    @property
    def live(self):
        return self.status == "published"

    @property
    def path(self):
        return url_path(self.slug)

    @property
    def draft_path(self):
        return f"/{DRAFT_DIR}/{self.token}/" if self.token else None


def load_pages():
    pages = [Page(p) for p in sorted(CONTENT.glob("*.md"))]
    seen = {}
    for p in pages:
        if p.slug in seen:
            raise SystemExit(f"duplicate slug {p.slug}: {p.file.name}, {seen[p.slug]}")
        seen[p.slug] = p.file.name
        if p.live and not p.published:
            raise SystemExit(f"{p.file.name}: published page needs a published date")
        if not p.live and not p.token:
            raise SystemExit(f"{p.file.name}: draft needs a token")
    return pages


# ---------- rendering ----------

def render_markdown(src):
    md = markdown.Markdown(
        extensions=["extra", "sane_lists", "toc"],
        extension_configs={"toc": {"slugify": slugify_unicode, "toc_depth": "2"}},
    )
    body = md.convert(src)
    toc = [(t["id"], t["name"]) for t in md.toc_tokens]
    return body, toc


def reading_minutes(src):
    words = len(re.findall(r"\S+", re.sub(r"[#>*_\-|`]", " ", src)))
    return max(1, math.ceil(words / 180))


def card(p):
    return (f'            <a class="article-card" href="{esc(p.path)}"><strong>{esc(p.title)}</strong>'
            f'<span>{esc(p.description)}</span></a>')


def render_page(p, pages, draft, hub_live, wa):
    by_slug = {x.slug: x for x in pages}
    body, toc = render_markdown(p.source)
    pillar = by_slug.get(p.pillar)
    g = p.meta.get

    crumbs = [("خانه", "/")]
    if hub_live:
        crumbs.append(("مقالات", f"/{HUB_DIR}/"))
    if p.type == "article" and pillar and pillar.live:
        crumbs.append((pillar.title, pillar.path))
    crumbs.append((p.title, None))
    breadcrumb = "\n".join(
        f'            <li><a href="{esc(u)}">{esc(t)}</a></li>' if u
        else f'            <li aria-current="page">{esc(t)}</li>'
        for t, u in crumbs)

    today = dt.date.today()
    pub, upd, rev = p.published, p.updated, p.reviewed
    if draft:
        dates = "پیش‌نویس، هنوز منتشر نشده"
    elif upd and upd != pub:
        dates = f"به‌روزرسانی: {jalali(upd)}"
    else:
        dates = f"انتشار: {jalali(pub)}"

    summary = ""
    if g("summary"):
        items = "\n".join(f"              <li>{esc(s)}</li>" for s in g("summary"))
        summary = (f'          <div class="summary-box">\n            <h2>خلاصه در یک نگاه</h2>\n'
                   f'            <ul>\n{items}\n            </ul>\n          </div>')

    faq_html, faq_ld = "", None
    if g("faq"):
        rows = []
        for i, f in enumerate(g("faq")):
            a_html = markdown.markdown(str(f["a"]))
            rows.append(f'              <details class="acc-item"{" open" if i == 0 else ""}>\n'
                        f'                <summary>{esc(f["q"])}</summary>\n'
                        f'                <div class="acc-body">{a_html}</div>\n'
                        f'              </details>')
        faq_html = ('          <div class="faq-block">\n            <h2 id="faq">پرسش‌های رایج</h2>\n'
                    '            <div class="accordion">\n' + "\n".join(rows) +
                    '\n            </div>\n          </div>')
        toc.append(("faq", "پرسش‌های رایج"))
        faq_ld = {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": f["q"],
             "acceptedAnswer": {"@type": "Answer", "text": re.sub(r"<[^>]+>", "", markdown.markdown(str(f["a"])))}}
            for f in g("faq")]}

    children = ""
    if p.type == "pillar":
        kids = [x for x in pages if x.live and x.type == "article" and x.pillar == p.slug]
        if kids:
            children = ('          <div class="related">\n            <h2 id="articles">مقالات این بخش</h2>\n'
                        '            <div class="card-list">\n' + "\n".join(card(k) for k in kids) +
                        '\n            </div>\n          </div>')
            toc.append(("articles", "مقالات این بخش"))

    rel_slugs = g("related") or []
    rel = [by_slug[s] for s in rel_slugs if s in by_slug and by_slug[s].live]
    if not rel and p.type == "article":
        rel = [x for x in pages if x.live and x is not p and x.type == "article" and x.pillar == p.pillar][:4]
        if pillar and pillar.live:
            rel = [pillar] + rel[:3]
    related = ""
    if rel:
        related = ('          <div class="related">\n            <h2>مطالب مرتبط</h2>\n'
                   '            <div class="card-list">\n' + "\n".join(card(r) for r in rel) +
                   '\n            </div>\n          </div>')

    review_panel = ""
    if draft:
        review_panel = fill(tpl("review-panel.html"), endpoint=ENDPOINT,
                            slug=esc(p.slug), title=esc(p.title))

    main = fill(
        tpl("article.html"),
        breadcrumb=breadcrumb,
        kicker=esc(g("kicker", "")),
        h1=esc(p.title),
        lead=esc(g("lead", p.description)),
        dates=dates,
        read_time=fa(reading_minutes(p.source)),
        toc="\n".join(f'              <li><a href="#{esc(i)}">{esc(n)}</a></li>' for i, n in toc),
        summary=summary,
        body=body,
        children=children,
        faq=faq_html,
        reviewed=("این مطلب پس از بازبینی علمی ایشان منتشر می‌شود." if draft
                  else f"این مطلب در تاریخ {jalali(rev or today)} توسط ایشان بازبینی علمی شده است."),
        cta_title=esc(g("cta", "برای بررسی وضعیت خود نوبت بگیرید")),
        review_panel=review_panel,
        related=related,
    )

    page_title = g("seo_title") or f"{p.title} | {DOCTOR}"
    image = g("image") or DEFAULT_IMAGE
    if draft:
        head = '  <meta name="robots" content="noindex, nofollow, noarchive">'
        schema, analytics = "", ""
        banner = ('  <div class="draft-banner">پیش‌نویس، هنوز منتشر نشده | '
                  '<a href="#review">رفتن به بخش تأیید</a></div>')
        scripts = '  <script src="/js/review.js"></script>'
    else:
        url = abs_url(p.path)
        head = "\n".join([
            f'  <link rel="canonical" href="{url}">',
            '  <meta name="robots" content="index, follow, max-image-preview:large">',
            '  <meta property="og:locale" content="fa_IR">',
            '  <meta property="og:type" content="article">',
            '  <meta property="og:site_name" content="دکتر نادر اکبری">',
            f'  <meta property="og:title" content="{esc(p.title)}">',
            f'  <meta property="og:description" content="{esc(p.description)}">',
            f'  <meta property="og:url" content="{url}">',
            f'  <meta property="og:image" content="{esc(image)}">',
            f'  <meta property="article:published_time" content="{pub.isoformat()}">',
            f'  <meta property="article:modified_time" content="{upd.isoformat()}">',
            '  <meta name="twitter:card" content="summary_large_image">',
        ])
        graph = [
            {"@type": "MedicalWebPage", "@id": url + "#page", "url": url, "name": p.title,
             "headline": p.title, "description": p.description, "inLanguage": "fa-IR",
             "image": image, "datePublished": pub.isoformat(), "dateModified": upd.isoformat(),
             "lastReviewed": (rev or upd).isoformat(),
             "author": {"@id": DOCTOR_ID}, "reviewedBy": {"@id": DOCTOR_ID},
             "publisher": {"@id": DOCTOR_ID}, "isPartOf": {"@id": SITE + "/#website"},
             "breadcrumb": {"@id": url + "#breadcrumb"}},
            {"@type": ["Physician", "Person"], "@id": DOCTOR_ID, "name": DOCTOR,
             "url": SITE + "/", "image": SITE + "/images/portrait.webp",
             "jobTitle": "دانشیار و فلوشیپ راینولوژی و جراحی قاعده جمجمه",
             "medicalSpecialty": ["Otolaryngology", "Rhinology"]},
            {"@type": "BreadcrumbList", "@id": url + "#breadcrumb", "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": t,
                 **({"item": abs_url(u)} if u else {})}
                for i, (t, u) in enumerate(crumbs)]},
        ]
        if g("about"):
            graph[0]["about"] = {"@type": "MedicalCondition", "name": g("about")}
        if faq_ld:
            graph.append(faq_ld)
        schema = json_ld({"@context": "https://schema.org", "@graph": graph})
        analytics = ANALYTICS
        banner, scripts = "", ""

    return layout(page_title, p.description, head, schema, analytics, main, banner, scripts,
                  hub_live, wa, "is-draft" if draft else "is-article")


def layout(title, description, head, schema, analytics, main, banner, scripts, hub_live, wa, body_class):
    nav = '        <a href="/مقالات/">مقالات</a>\n' if hub_live else ""
    return fill(tpl("layout.html"), title=esc(title), description=esc(description), head=head,
                schema=schema, analytics=analytics, main=main, banner=banner, scripts=scripts,
                nav_articles=nav, sheet_articles=nav, wa_path=wa, body_class=body_class)


def redirect_page(target):
    t = esc(target)
    return ('<!DOCTYPE html>\n<html lang="fa-IR" dir="rtl">\n<head>\n  <meta charset="UTF-8">\n'
            '  <meta name="robots" content="noindex">\n'
            f'  <link rel="canonical" href="{abs_url(target)}">\n'
            f'  <meta http-equiv="refresh" content="0; url={t}">\n'
            '  <title>انتقال به مقاله منتشرشده</title>\n</head>\n<body>\n'
            f'  <p>این پیش‌نویس منتشر شده است: <a href="{t}">مشاهده مقاله</a></p>\n'
            f'  <script>location.replace({json.dumps(target, ensure_ascii=False)});</script>\n'
            '</body>\n</html>\n')


def render_hub(pages, wa):
    live = [p for p in pages if p.live]
    pillars = [p for p in live if p.type == "pillar"]
    groups = []
    for pl in pillars:
        kids = [p for p in live if p.type == "article" and p.pillar == pl.slug]
        groups.append(f'        <div class="hub-group">\n          <h2><a href="{esc(pl.path)}">{esc(pl.title)}</a></h2>\n'
                      f'          <div class="card-list">\n' + "\n".join(card(k) for k in [pl] + kids) +
                      '\n          </div>\n        </div>')
    pillar_slugs = {pl.slug for pl in pillars}
    rest = [p for p in live if p.type == "article" and p.pillar not in pillar_slugs]
    if rest:
        groups.append('        <div class="hub-group">\n          <h2>سایر مقالات</h2>\n'
                      '          <div class="card-list">\n' + "\n".join(card(k) for k in rest) +
                      '\n          </div>\n        </div>')
    url = abs_url(f"/{HUB_DIR}/")
    desc = "مقالات آموزشی درباره سینوزیت، پولیپ بینی، جراحی قاعده جمجمه و رینوپلاستی، بازبینی‌شده توسط دکتر نادر اکبری دیلمقانی."
    head = "\n".join([
        f'  <link rel="canonical" href="{url}">',
        '  <meta name="robots" content="index, follow, max-image-preview:large">',
        '  <meta property="og:locale" content="fa_IR">',
        '  <meta property="og:type" content="website">',
        '  <meta property="og:title" content="مقالات دکتر نادر اکبری">',
        f'  <meta property="og:description" content="{esc(desc)}">',
        f'  <meta property="og:url" content="{url}">',
        f'  <meta property="og:image" content="{DEFAULT_IMAGE}">',
    ])
    schema = json_ld({"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "@id": url + "#page", "url": url, "name": "مقالات دکتر نادر اکبری",
         "inLanguage": "fa-IR", "isPartOf": {"@id": SITE + "/#website"}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "خانه", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "مقالات"}]},
    ]})
    main = fill(tpl("hub.html"), groups="\n".join(groups))
    return layout(f"مقالات | {DOCTOR}", desc, head, schema, ANALYTICS, main, "", "", True, wa, "is-hub")


def render_sitemap(pages, hub_live):
    rows = [(path, prio, None) for path, prio in STATIC_PAGES]
    live = [p for p in pages if p.live]
    if hub_live:
        rows.append((f"/{HUB_DIR}/", "0.7", max(p.updated for p in live)))
    for p in live:
        rows.append((p.path, "0.9" if p.type == "pillar" else "0.7", p.updated))
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, prio, mod in rows:
        out.append("  <url>")
        out.append(f"    <loc>{abs_url(path)}</loc>")
        if mod:
            out.append(f"    <lastmod>{mod.isoformat()}</lastmod>")
        out.append(f"    <priority>{prio}</priority>")
        out.append("  </url>")
    out.append("</urlset>")
    return "\n".join(out) + "\n"


def check_links(rel_file, text, known):
    for href in re.findall(r'href="(/[^"#?]*)', text):
        if href in known or href.startswith(("/css/", "/js/", "/images/", "/fonts/")):
            continue
        if not (ROOT / href.strip("/")).exists():
            print(f"  warning: {rel_file} links to missing page {href}")


def build():
    pages = load_pages()
    wa = wa_path()
    hub_live = any(p.live for p in pages)
    outputs = {}
    known = {"/", f"/{HUB_DIR}/"} | {p.path for p in pages if p.live}

    for p in pages:
        if p.live:
            outputs[f"{p.slug}/index.html"] = render_page(p, pages, False, hub_live, wa)
            if p.token:
                outputs[f"{DRAFT_DIR}/{p.token}/index.html"] = redirect_page(p.path)
        else:
            outputs[f"{DRAFT_DIR}/{p.token}/index.html"] = render_page(p, pages, True, hub_live, wa)
    if hub_live:
        outputs[f"{HUB_DIR}/index.html"] = render_hub(pages, wa)
    outputs["sitemap.xml"] = render_sitemap(pages, hub_live)

    old = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else []
    for rel in old:
        if rel not in outputs and rel != "sitemap.xml":
            f = ROOT / rel
            if f.exists():
                f.unlink()
                print(f"  removed {rel}")
            d = f.parent
            while d != ROOT and d.exists() and not any(d.iterdir()):
                d.rmdir()
                d = d.parent

    for rel, text in outputs.items():
        f = ROOT / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text, encoding="utf-8", newline="\n")
        if rel.endswith(".html"):
            check_links(rel, text, known)
    MANIFEST.write_text(json.dumps(sorted(outputs), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for p in pages:
        state = "منتشر" if p.live else "پیش‌نویس"
        url = abs_url(p.path) if p.live else abs_url(p.draft_path)
        print(f"  [{state}] {p.title}\n           {SITE}{p.path if p.live else p.draft_path}  ({url})")
    print(f"built {len(outputs)} files")


# ---------- commands ----------

def cmd_new(args):
    if len(args) < 2:
        raise SystemExit('usage: new <slug> "<title>" [--pillar <slug>] [--type pillar]')
    slug, title = args[0].strip("/"), args[1]
    opts = dict(zip(args[2::2], args[3::2]))
    f = CONTENT / f"{slug}.md"
    if f.exists():
        raise SystemExit(f"{f.name} already exists")
    CONTENT.mkdir(exist_ok=True)
    fm = {
        "title": title,
        "slug": slug,
        "type": opts.get("--type", "article"),
        "pillar": opts.get("--pillar", ""),
        "kicker": "",
        "description": "",
        "lead": "",
        "about": "",
        "status": "draft",
        "token": secrets.token_hex(6),
        "published": None,
        "updated": None,
        "reviewed": None,
        "summary": [],
        "faq": [],
        "related": [],
    }
    f.write_text("---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) +
                 "---\n\n## عنوان بخش اول\n\nمتن...\n", encoding="utf-8", newline="\n")
    print(f"created {f.relative_to(ROOT)}\ndraft url: {SITE}/{DRAFT_DIR}/{fm['token']}/")


def set_front(f, changes):
    raw = f.read_text(encoding="utf-8").replace("\r\n", "\n")
    for k, v in changes.items():
        raw, n = re.subn(rf"^{k}:.*$", f"{k}: {v}", raw, count=1, flags=re.M)
        if not n:
            raw = raw.replace("---\n", f"---\n{k}: {v}\n", 1)
    f.write_text(raw, encoding="utf-8", newline="\n")


def cmd_publish(args):
    if not args:
        raise SystemExit("usage: publish <slug>")
    p = next((x for x in load_pages() if x.slug == args[0].strip("/")), None)
    if not p:
        raise SystemExit("not found")
    today = dt.date.today().isoformat()
    changes = {"status": "published", "updated": today, "reviewed": today}
    if not p.published:
        changes["published"] = today
    set_front(p.file, changes)
    print(f"published {p.slug}; run build")


def cmd_list(_):
    for p in load_pages():
        where = p.path if p.live else p.draft_path
        print(f"{p.status:9} {p.type:7} {SITE}{where}  {p.title}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    cmd, rest = (sys.argv[1], sys.argv[2:]) if len(sys.argv) > 1 else ("build", [])
    {"build": lambda _: build(), "new": cmd_new, "publish": cmd_publish, "list": cmd_list}[cmd](rest)
