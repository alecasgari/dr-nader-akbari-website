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
from PIL import Image

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
HUB_DIR = "بلاگ"
HUB_LEGACY = "مقالات"
PUB_DIR = "مقالات-علمی"
PUB_DATA = ROOT / PUB_DIR / "data" / "index.json"
SCHOLAR_URL = "https://scholar.google.com/citations?user=13wD0fwAAAAJ&hl=en"
DEFAULT_IMAGE = SITE + "/images/hero.webp"
VIDEO_DIR = "ویدیو"
VIDEOS_DATA = CONTENT / "videos.yaml"
VIDEO_OG = "/images/videos/og.jpg"
VIDEO_SHARE = (
    '            <div class="vg-share" data-vg-share>\n'
    '              <span class="vg-share-label">اشتراک‌گذاری</span>\n'
    '              <a class="vg-share-btn" data-share="telegram" target="_blank" rel="noopener" aria-label="تلگرام">'
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M21.5 3.6 18.9 20c-.2 1-1.2 1.4-2 .9l-5.3-4-2.6 2.5c-.3.3-.8.1-.9-.3L7 14.2 3.2 13c-1-.3-1-1.7.1-2l17.3-8.1c.9-.4 1.8.4 1.4 1.7zM9.7 13.7l.6 4.6 1.4-2.7 7.2-6.5-9.2 4.6z"/></svg></a>\n'
    '              <a class="vg-share-btn" data-share="whatsapp" target="_blank" rel="noopener" aria-label="واتساپ">'
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12.04 2C6.58 2 2.15 6.4 2.15 11.84c0 1.74.46 3.44 1.33 4.94L2 22l5.37-1.4a10 10 0 0 0 4.67 1.15h.01c5.46 0 9.89-4.4 9.89-9.85C21.94 6.4 17.5 2 12.04 2m5.76 14.08c-.24.68-1.4 1.26-1.94 1.3-.5.04-1.13.06-1.82-.11-.42-.11-.96-.31-1.66-.61-2.92-1.26-4.82-4.2-4.97-4.4-.14-.19-1.18-1.57-1.18-3 0-1.41.74-2.11 1-2.4.24-.27.64-.39 1.02-.39h.73c.23 0 .55-.09.86.66.33.79 1.11 2.72 1.21 2.92.1.19.16.42.03.68-.13.27-.2.43-.4.66-.19.23-.42.51-.6.69-.19.19-.38.39-.16.76.22.37 1 1.64 2.14 2.66 1.47 1.31 2.71 1.72 3.1 1.91.38.19.61.16.84-.1.22-.25.97-1.13 1.23-1.52.26-.38.52-.32.88-.19.36.13 2.32 1.09 2.72 1.29.4.2.66.3.76.47.09.16.09.95-.15 1.63z"/></svg></a>\n'
    '              <button type="button" class="vg-share-btn" data-share="copy" aria-label="کپی لینک">'
    '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="none" stroke="currentColor" stroke-width="2" d="M9 9h9v11H9z"/><path fill="none" stroke="currentColor" stroke-width="2" d="M6 15H5V4h9v1"/></svg></button>\n'
    '            </div>\n'
)
STATIC_PAGES = [("/", "1.0"), ("/دستورالعمل/", "0.8")]

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


WA_PATH = ("M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347"
           "m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.435 9.884-9.885 9.884"
           "m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z")

ANALYTICS = tpl("analytics.html").replace("\r\n", "\n").rstrip("\n")
GTM_NOSCRIPT = ('  <noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-N5FRJM47" '
                'height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>\n')

# Hand-written pages filled in from the shared templates; None = analytics only, no header/footer.
STATIC_CHROME = {"index.html": "/", "دستورالعمل/index.html": "/دستورالعمل/", "404.html": None}


def page_category(p):
    g = p.meta.get
    if g("category"):
        return str(g("category")).strip()
    if g("kicker"):
        return str(g("kicker")).strip()
    return "راهنمای درمان" if p.type == "pillar" else "مقالات"


def page_excerpt(p):
    g = p.meta.get
    return str(g("description") or g("lead") or "").strip()


def page_search_blob(p):
    body = re.sub(r"^---\n.*?\n---\n", "", p.source, flags=re.S)
    body = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", body)
    body = re.sub(r"\{[^}]+\}", "", body)
    body = re.sub(r"[#>*_\[\]|`-]", " ", body)
    body = re.sub(r"\s+", " ", body).strip()
    parts = [p.title, page_category(p), page_excerpt(p), body[:1200]]
    return " ".join(parts)


def load_publications_bundle():
    if not PUB_DATA.is_file():
        return None
    return json.loads(PUB_DATA.read_text(encoding="utf-8"))


def publications_live():
    data = load_publications_bundle()
    return bool(data and data.get("publications"))


def load_videos():
    if not VIDEOS_DATA.is_file():
        return []
    return yaml.safe_load(VIDEOS_DATA.read_text(encoding="utf-8")) or []


def iso_duration(seconds):
    seconds = int(seconds or 0)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"PT{h}H{m}M{s}S"
    if m:
        return f"PT{m}M{s}S"
    return f"PT{s}S"


def clock_label(seconds):
    seconds = int(seconds or 0)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{fa(h)}:{fa(f'{m:02d}')}:{fa(f'{s:02d}')}"
    return f"{fa(m)}:{fa(f'{s:02d}')}"


def video_related(v, pages):
    by_slug = {p.slug: p for p in pages if p.live}
    items = []
    for slug in v.get("related") or []:
        p = by_slug.get(slug)
        if p:
            items.append({"href": p.path, "title": str(p.meta.get("nav_title") or p.title)})
    return items


def video_payload(videos, pages):
    out = []
    for v in videos:
        body_html = markdown.markdown(v.get("body") or "", extensions=["extra", "sane_lists"])
        out.append({
            "id": v["id"],
            "slug": v["slug"],
            "path": f"/{VIDEO_DIR}/{v['slug']}/",
            "kicker": v.get("kicker") or "",
            "title": v["title"],
            "description": v.get("description") or "",
            "src": v["src"],
            "poster": v["poster"],
            "instagram": v.get("instagram") or "",
            "duration": int(v.get("duration") or 0),
            "related": video_related(v, pages),
            "bodyHtml": body_html,
        })
    return out


def video_tile(v):
    title = esc(v["title"])
    poster = esc(v["poster"])
    href = f"/{VIDEO_DIR}/{v['slug']}/"
    return (
        f'          <a class="vg-tile" href="{href}" data-id="{esc(v["id"])}" '
        f'data-src="{esc(v["src"])}" data-kicker="{esc(v.get("kicker") or "")}">\n'
        f'            <span class="vg-tile-media">\n'
        f'              <img src="{poster}" width="{int(v.get("poster_w") or 720)}" '
        f'height="{int(v.get("poster_h") or 1280)}" alt="{title}" loading="lazy" decoding="async">\n'
        f'              <video muted loop playsinline preload="none"></video>\n'
        f'            </span>\n'
        f'            <span class="vg-tile-play" aria-hidden="true"></span>\n'
        f'            <span class="vg-tile-time">{clock_label(v.get("duration"))}</span>\n'
        f'            <span class="vg-tile-cap"><b>{esc(v.get("kicker") or "")}</b>'
        f'<strong>{title}</strong></span>\n'
        f'          </a>'
    )


def video_filters(videos):
    cats = []
    for v in videos:
        k = (v.get("kicker") or "").strip()
        if k and k not in cats:
            cats.append(k)
    buttons = ['            <button type="button" class="is-active" data-filter="all">همه</button>']
    for c in cats:
        buttons.append(f'            <button type="button" data-filter="{esc(c)}">{esc(c)}</button>')
    return "\n".join(buttons)


def render_video_pages(pages, hub_live):
    videos = load_videos()
    if not videos:
        return {}
    payload = video_payload(videos, pages)
    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    grid = "\n".join(video_tile(v) for v in videos)
    filters = video_filters(videos)
    scripts = '  <script src="/js/videos.js" defer></script>\n'
    hub_path = f"/{VIDEO_DIR}/"
    hub_title = f"ویدیوهای آموزشی بینی و سینوس | {DOCTOR}"
    hub_desc = ("ویدیو آموزشی سینوزیت، پولیپ بینی، نشت مایع مغزی نخاعی، درد گوش و "
                "جراحی آندوسکوپی سینوس با توضیح فارسی برای پرسش‌های رایج گوگل.")
    hub_lead = ("فیلم‌های کوتاه آموزشی درباره بینی، سینوس و قاعده جمجمه. هر ویدیو را "
                "بزنید تا با توضیح علائم، تشخیص و درمان باز شود.")
    hub_crumbs = "\n".join([
        '            <li><a href="/">خانه</a></li>',
        '            <li aria-current="page">ویدیو</li>',
    ])
    og = SITE + VIDEO_OG
    list_items = [{"@type": "ListItem", "position": i + 1,
                   "url": abs_url(f"/{VIDEO_DIR}/{v['slug']}/"), "name": v["title"]}
                  for i, v in enumerate(videos)]
    hub_faqs = [
        {"q": "ویدیوهای آموزشی بینی و سینوس را از کجا ببینم؟",
         "a": "آرشیو ویدیوهای آموزشی دکتر نادر اکبری در صفحه ویدیو سایت است؛ پخش از سرور خود مطب انجام می‌شود و وابسته به اینستاگرام نیست."},
        {"q": "آبریزش شفاف یک‌طرفه بینی خطرناک است؟",
         "a": "آبریزش زلال یک‌طرفه، به‌ویژه با خم شدن سر، می‌تواند نشت مایع مغزی نخاعی باشد نه فقط آلرژی. تشخیص دیرهنگام خطر مننژیت دارد و باید توسط فلوشیپ راینولوژی بررسی شود."},
        {"q": "پولیپ بینی با انحراف تیغه چه فرقی دارد؟",
         "a": "پولیپ بینی بافت ملتهب نرم و معمولاً دوطرفه است و بویایی را کم می‌کند؛ انحراف تیغه مشکل استخوانی یک‌طرفه است. درمان پولیپوز اغلب دارویی و در موارد انسدادی جراحی آندوسکوپی سینوس است."},
        {"q": "سردرد پیشانی همان میگرن است یا سینوزیت فرونتال؟",
         "a": "اگر درد بالای چشم با گرفتگی بینی، ترشح پشت حلق یا فشار هنگام خم شدن همراه باشد، سینوزیت فرونتال محتمل‌تر از میگرن خالص است و تصویربرداری و آندوسکوپی کمک می‌کند."},
    ]
    faq_html = "\n".join(
        f'          <details class="acc-item"><summary>{esc(x["q"])}</summary>'
        f'<div class="acc-body"><p>{esc(x["a"])}</p></div></details>'
        for x in hub_faqs
    )
    below = (
        '    <section class="article-section vg-guide">\n'
        '      <div class="wrap">\n'
        '        <h2>ویدیو آموزشی برای پرسش‌های رایج بیماران</h2>\n'
        '        <p class="lead">این صفحه برای کسانی است که در گوگل «نشت مایع مغزی از بینی»، «پولیپ بینی»، '
        '«سینوزیت فرونتال»، «علت درد گوش» یا «جراحی آندوسکوپی سینوس» را جستجو می‌کنند و می‌خواهند توضیح '
        'کوتاه متخصص را ببینند، بعد متن کامل همان موضوع را بخوانند.</p>\n'
        '        <p>پخش فیلم‌ها روی دامنه خود سایت است. زیر هر ویدیو متن بازنویسی‌شده برای همان کوئری آمده '
        'و به صفحات راهنما لینک می‌شود: '
        '<a href="/جراحی-آندوسکوپی-سینوس/">جراحی آندوسکوپی سینوس</a>، '
        '<a href="/پولیپ-بینی/">پولیپ بینی</a>، '
        '<a href="/سینوزیت-مزمن/">سینوزیت مزمن</a> و '
        '<a href="/شستشوی-بینی-با-سرم/">شستشوی بینی با سرم</a>.</p>\n'
        '        <div class="faq-block">\n'
        '          <h2 id="faq">پرسش‌های رایج درباره این ویدیوها</h2>\n'
        f'          <div class="accordion">\n{faq_html}\n          </div>\n'
        '        </div>\n'
        '      </div>\n'
        '    </section>\n'
    )
    hub_head = "\n".join([
        f'  <link rel="canonical" href="{abs_url(hub_path)}">',
        '  <meta name="robots" content="index, follow, max-image-preview:large, max-video-preview:-1">',
        '  <meta property="og:locale" content="fa_IR">',
        '  <meta property="og:type" content="website">',
        '  <meta property="og:site_name" content="دکتر نادر اکبری">',
        f'  <meta property="og:title" content="{esc(hub_title)}">',
        f'  <meta property="og:description" content="{esc(hub_desc)}">',
        f'  <meta property="og:url" content="{abs_url(hub_path)}">',
        f'  <meta property="og:image" content="{esc(og)}">',
        '  <meta property="og:image:width" content="1200">',
        '  <meta property="og:image:height" content="630">',
        '  <meta property="og:image:alt" content="ویدیوهای آموزشی بینی و سینوس دکتر نادر اکبری">',
        '  <meta name="twitter:card" content="summary_large_image">',
        f'  <meta name="twitter:title" content="{esc(hub_title)}">',
        f'  <meta name="twitter:description" content="{esc(hub_desc)}">',
        f'  <meta name="twitter:image" content="{esc(og)}">',
    ])
    video_list = []
    for i, v in enumerate(videos):
        video_list.append({
            "@type": "VideoObject", "position": i + 1, "name": v["title"],
            "description": v.get("description") or v["title"],
            "thumbnailUrl": SITE + v["poster"], "contentUrl": v["src"],
            "url": abs_url(f"/{VIDEO_DIR}/{v['slug']}/"),
            "uploadDate": str(v.get("date") or "2026-10-10"),
            "duration": iso_duration(v.get("duration")), "inLanguage": "fa",
        })
    hub_schema = json_ld({"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "@id": abs_url(hub_path) + "#page", "url": abs_url(hub_path),
         "name": "ویدیوهای آموزشی بینی و سینوس", "description": hub_desc,
         "inLanguage": "fa-IR", "isPartOf": {"@id": SITE + "/#website"},
         "primaryImageOfPage": {"@type": "ImageObject", "url": og, "width": 1200, "height": 630},
         "about": [{"@type": "MedicalCondition", "name": n} for n in
                   ["نشت مایع مغزی نخاعی", "پولیپ بینی", "سینوزیت", "درد گوش"]],
         "mainEntity": {"@type": "ItemList", "numberOfItems": len(videos),
                        "itemListElement": list_items}},
        {"@type": "ItemList", "@id": abs_url(hub_path) + "#videos",
         "itemListElement": video_list},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": x["q"],
             "acceptedAnswer": {"@type": "Answer", "text": x["a"]}} for x in hub_faqs]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "خانه", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "ویدیو"}]},
        {"@type": ["Physician", "Person"], "@id": DOCTOR_ID, "name": DOCTOR, "url": SITE + "/"},
    ]})
    hub_main = fill(tpl("videos.html"), breadcrumb=hub_crumbs, kicker="آرشیو ویدیو",
                    h1="ویدیوهای آموزشی بینی، سینوس و قاعده جمجمه", lead=hub_lead,
                    watch="", below=below, count=fa(len(videos)), filters=filters, grid=grid,
                    videos_json=payload_json)
    out = {f"{VIDEO_DIR}/index.html": layout(
        hub_title, hub_desc, hub_head, hub_schema, ANALYTICS, hub_main, "", scripts,
        hub_live, hub_path, "is-videos is-videos-hub", pages)}

    by_id = {p["id"]: p for p in payload}
    for v in videos:
        path = f"/{VIDEO_DIR}/{v['slug']}/"
        url = abs_url(path)
        poster = SITE + v["poster"]
        title = f"{v['title']} | {DOCTOR}"
        desc = v.get("description") or v["title"]
        body_html = by_id[v["id"]]["bodyHtml"]
        rel = by_id[v["id"]]["related"]
        links = []
        for r in rel:
            links.append(f'            <a href="{esc(r["href"])}">{esc(r["title"])}</a>')
        if v.get("instagram"):
            links.append(f'            <a href="{esc(v["instagram"])}" target="_blank" rel="noopener">پست اینستاگرام</a>')
        watch = (
            '    <section class="vg-watch wrap">\n'
            '      <div class="vg-watch-player">\n'
            f'        <video controls playsinline controlslist="nodownload" poster="{esc(v["poster"])}" '
            f'src="{esc(v["src"])}" title="{esc(v["title"])}"></video>\n'
            '      </div>\n'
            '      <div class="vg-watch-copy">\n'
            + VIDEO_SHARE +
            f'            <p class="kicker">{esc(v.get("kicker") or "")}</p>\n'
            f'        <div class="vg-watch-body">{body_html}</div>\n'
            '        <div class="vg-watch-links">\n' + "\n".join(links) + "\n        </div>\n"
            "      </div>\n    </section>\n"
        )
        crumbs = "\n".join([
            '            <li><a href="/">خانه</a></li>',
            f'            <li><a href="{hub_path}">ویدیو</a></li>',
            f'            <li aria-current="page">{esc(v["title"])}</li>',
        ])
        transcript = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body_html)).strip()
        head = "\n".join([
            f'  <link rel="canonical" href="{url}">',
            '  <meta name="robots" content="index, follow, max-image-preview:large, max-video-preview:-1">',
            '  <meta property="og:locale" content="fa_IR">',
            '  <meta property="og:type" content="video.other">',
            '  <meta property="og:site_name" content="دکتر نادر اکبری">',
            f'  <meta property="og:title" content="{esc(v["title"])}">',
            f'  <meta property="og:description" content="{esc(desc)}">',
            f'  <meta property="og:url" content="{url}">',
            f'  <meta property="og:image" content="{esc(og)}">',
            '  <meta property="og:image:width" content="1200">',
            '  <meta property="og:image:height" content="630">',
            f'  <meta property="og:video" content="{esc(v["src"])}">',
            '  <meta property="og:video:type" content="video/mp4">',
            '  <meta name="twitter:card" content="summary_large_image">',
            f'  <meta name="twitter:title" content="{esc(v["title"])}">',
            f'  <meta name="twitter:description" content="{esc(desc)}">',
            f'  <meta name="twitter:image" content="{esc(og)}">',
        ])
        video_obj = {
            "@type": "VideoObject",
            "@id": url + "#video",
            "name": v["title"],
            "description": desc,
            "thumbnailUrl": [poster, og],
            "contentUrl": v["src"],
            "embedUrl": url,
            "uploadDate": str(v.get("date") or "2026-10-10"),
            "duration": iso_duration(v.get("duration")),
            "inLanguage": "fa",
            "transcript": transcript[:5000],
            "author": {"@id": DOCTOR_ID},
            "publisher": {"@id": DOCTOR_ID},
            "isFamilyFriendly": True,
        }
        schema = json_ld({"@context": "https://schema.org", "@graph": [
            {"@type": "WebPage", "@id": url + "#page", "url": url, "name": v["title"],
             "description": desc, "inLanguage": "fa-IR",
             "primaryImageOfPage": {"@type": "ImageObject", "url": og, "width": 1200, "height": 630},
             "mainEntity": {"@id": url + "#video"}, "isPartOf": {"@id": SITE + "/#website"},
             "breadcrumb": {"@id": url + "#breadcrumb"}},
            video_obj,
            {"@type": "BreadcrumbList", "@id": url + "#breadcrumb", "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "خانه", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "ویدیو", "item": abs_url(hub_path)},
                {"@type": "ListItem", "position": 3, "name": v["title"]}]},
            {"@type": ["Physician", "Person"], "@id": DOCTOR_ID, "name": DOCTOR, "url": SITE + "/"},
        ]})
        main = fill(tpl("videos.html"), breadcrumb=crumbs, kicker="ویدیوی آموزشی",
                    h1=esc(v["title"]), lead=esc(desc), watch=watch, below="",
                    count=fa(len(videos)), filters=filters, grid=grid,
                    videos_json=payload_json)
        out[f"{VIDEO_DIR}/{v['slug']}/index.html"] = layout(
            title, desc, head, schema, ANALYTICS, main, "", scripts,
            hub_live, path, "is-videos", pages)
    return out


def services_nav(pages):
    pillars = sorted((x for x in pages if x.live and x.type == "pillar"), key=lambda x: x.title)
    items = ['          <a href="/#services">نمای کلی خدمات</a>']
    for p in pillars:
        label = str(p.meta.get("nav_title") or p.title).strip()
        items.append(f'          <a href="{p.path}">{esc(label)}</a>')
    inner = "\n".join(items)
    return (
        '        <div class="nav-drop">\n'
        '          <a href="/#services" class="nav-drop-toggle" aria-expanded="false">خدمات</a>\n'
        f'          <div class="nav-drop-menu">\n{inner}\n          </div>\n'
        '        </div>'
    )


def build_nav(current, hub_live, pages):
    lines = [
        '        <a href="/">خانه</a>',
        '        <a href="/#about">درباره</a>',
        services_nav(pages),
    ]
    if hub_live:
        lines.append(f'        <a href="/{HUB_DIR}/">بلاگ</a>')
    if publications_live():
        lines.append(f'        <a href="/{PUB_DIR}/">مقالات علمی</a>')
    lines += [
        '        <a href="/دستورالعمل/">دستورالعمل</a>',
        f'        <a href="/{VIDEO_DIR}/">ویدیو</a>',
        '        <a href="/#contact">تماس</a>',
    ]
    nav = "\n".join(lines)
    if current:
        if current.rstrip("/").startswith("/" + VIDEO_DIR):
            nav = nav.replace(f'href="/{VIDEO_DIR}/">', f'href="/{VIDEO_DIR}/" aria-current="page">', 1)
        else:
            nav = nav.replace(f'href="{current}">', f'href="{current}" aria-current="page">', 1)
    return nav


def site_chrome(current, hub_live, pages, tracking=True):
    nav = build_nav(current, hub_live, pages)
    header = fill(tpl("header.html"), nav=nav, wa_path=WA_PATH).replace("\r\n", "\n")
    footer = fill(tpl("footer.html"), nav=nav, wa_path=WA_PATH).replace("\r\n", "\n")
    return (GTM_NOSCRIPT if tracking else "") + header, footer


def patch_homepage_publications(hub_live, pages):
    data = load_publications_bundle()
    if not data:
        return
    total = int(data.get("stats", {}).get("total") or 0)
    if total <= 0:
        return
    f = ROOT / "index.html"
    raw = f.read_bytes().decode("utf-8")
    eol = "\r\n" if "\r\n" in raw else "\n"
    text = raw.replace("\r\n", "\n")
    stat_pat = re.compile(
        r'(?:<a class="stat-pub-link" href="/' + PUB_DIR + r'/">\s*)?'
        r'<div class="stat reveal"><b data-count="\d+"[^>]*>[^<]*</b>'
        r'<span>مقاله(?: علمی منتشرشده| منتشر شده)</span></div>'
        r'(?:\s*</a>)?',
        re.S,
    )
    stat_block = (
        f'<a class="stat-pub-link" href="/{PUB_DIR}/">'
        f'<div class="stat reveal"><b data-count="{total}" data-count-suffix="" '
        f'data-count-locale="fa-IR">{fa(total)}</b><span>مقاله علمی منتشرشده</span></div></a>'
    )
    if stat_pat.search(text):
        text = stat_pat.sub(stat_block, text, count=1)
    scholar = SCHOLAR_URL
    if '"sameAs"' not in text:
        text = text.replace(
            '"medicalSpecialty":["Otolaryngology","Rhinology"],',
            '"medicalSpecialty":["Otolaryngology","Rhinology"],'
            f'"sameAs":["{scholar}"],',
            1,
        )
    blocks = [("analytics", ANALYTICS + "\n")]
    blocks += list(zip(("site-header", "site-footer"), site_chrome("/", hub_live, pages)))
    for name, block in blocks:
        pat = re.compile(rf"(  <!-- {name} -->\n).*?(  <!-- /{name} -->\n)", re.S)
        if pat.search(text):
            text = pat.sub(lambda m: m.group(1) + block + m.group(2), text, count=1)
    out = text.replace("\n", eol)
    if out != raw:
        f.write_bytes(out.encode("utf-8"))
        print(f"  updated homepage publications ({total})")


def apply_static_chrome(hub_live, pages):
    patch_homepage_publications(hub_live, pages)
    for rel, current in STATIC_CHROME.items():
        f = ROOT / rel
        raw = f.read_bytes().decode("utf-8")
        eol = "\r\n" if "\r\n" in raw else "\n"
        text = raw.replace("\r\n", "\n")
        blocks = [("analytics", ANALYTICS + "\n")]
        if current:
            blocks += list(zip(("site-header", "site-footer"), site_chrome(current, hub_live, pages)))
        for name, block in blocks:
            pat = re.compile(rf"(  <!-- {name} -->\n).*?(  <!-- /{name} -->\n)", re.S)
            if not pat.search(text):
                raise SystemExit(f"{rel}: missing <!-- {name} --> markers")
            text = pat.sub(lambda m: m.group(1) + block + m.group(2), text, count=1)
        out = text.replace("\n", eol)
        if out != raw:
            f.write_bytes(out.encode("utf-8"))
            print(f"  updated shared blocks in {rel}")


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

def image_size(src):
    with Image.open(ROOT / src.lstrip("/")) as im:
        return im.size


def size_images(body):
    def fix(m):
        tag = m.group(0)
        src = re.search(r'src="(/[^"]+)"', tag)
        if not src or " width=" in tag:
            return tag
        w, h = image_size(src.group(1))
        return tag[:-1].rstrip(" /") + f' width="{w}" height="{h}" loading="lazy" decoding="async">'
    body = re.sub(r"<img [^>]+>", fix, body)
    return re.sub(r"<p>(<img [^>]+>)</p>", r'<figure>\1</figure>', body)


def render_markdown(src):
    md = markdown.Markdown(
        extensions=["extra", "sane_lists", "toc"],
        extension_configs={"toc": {"slugify": slugify_unicode, "toc_depth": "2"}},
    )
    body = size_images(md.convert(src))
    toc = [(t["id"], t["name"]) for t in md.toc_tokens]
    return body, toc


def reading_minutes(src):
    words = len(re.findall(r"\S+", re.sub(r"[#>*_\-|`]", " ", src)))
    return max(1, math.ceil(words / 180))


def card(p):
    return (f'            <a class="article-card" href="{esc(p.path)}"><strong>{esc(p.title)}</strong>'
            f'<span>{esc(p.description)}</span></a>')


def hub_card(p):
    cat = esc(page_category(p))
    excerpt = esc(page_excerpt(p))
    kind = "صفحه راهنما" if p.type == "pillar" else "مقاله"
    date = jalali(p.updated or p.published) if (p.updated or p.published) else ""
    meta = f"{kind}" + (f" · {date}" if date else "")
    search = esc(page_search_blob(p))
    img = p.meta.get("image") or ""
    media = ""
    if img:
        w, h = image_size(str(img))
        media = (f'              <div class="blog-card-media">\n'
                 f'                <img src="{esc(img)}" width="{w}" height="{h}" alt="" loading="lazy" '
                 f'decoding="async">\n              </div>\n')
    return (f'          <article class="blog-card" data-category="{cat}" data-search="{search}">\n'
            f'            <a class="blog-card-link" href="{esc(p.path)}">\n{media}'
            f'              <div class="blog-card-body">\n'
            f'                <span class="blog-badge">{cat}</span>\n'
            f'                <h2 class="blog-card-title">{esc(p.title)}</h2>\n'
            f'                <p class="blog-card-excerpt">{excerpt}</p>\n'
            f'                <p class="blog-card-meta">{esc(meta)}</p>\n'
            f'              </div>\n            </a>\n          </article>')


def render_page(p, pages, draft, hub_live):
    by_slug = {x.slug: x for x in pages}
    asks = re.findall(r"\[\[(.+?)\]\]", p.source)
    if asks and not draft:
        raise SystemExit(f"{p.file.name}: {len(asks)} open doctor questions; resolve [[...]] before publishing")
    body, toc = render_markdown(p.source)
    body = re.sub(r"\[\[(.+?)\]\]", lambda m: f'<mark class="ask"><b>پرسش از دکتر:</b> {m.group(1)}</mark>', body)
    if draft:
        for x in pages:
            if not x.live:
                body = body.replace(f'href="{x.path}"', f'href="{x.draft_path}"')
    pillar = by_slug.get(p.pillar)
    g = p.meta.get

    crumbs = [("خانه", "/")]
    if hub_live:
        crumbs.append(("بلاگ", f"/{HUB_DIR}/"))
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
    comments = fill(tpl("comments.html"), endpoint=ENDPOINT, slug=esc(p.slug),
                    title=esc(p.title), preview="1" if draft else "0")

    hero_image = ""
    if g("image"):
        w, h = image_size(g("image"))
        hero_image = (f'          <figure class="article-figure">\n'
                      f'            <img src="{esc(g("image"))}" width="{w}" height="{h}" '
                      f'alt="{esc(g("image_alt", p.title))}" fetchpriority="high">\n'
                      f'          </figure>')

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
        comments=comments,
        hero_image=hero_image,
        instr_download=tpl("instr-download.html") if p.slug == "دستورالعمل" else "",
    )

    page_title = g("seo_title") or f"{p.title} | {DOCTOR}"
    image = SITE + (g("og_image") or g("image")) if (g("og_image") or g("image")) else DEFAULT_IMAGE
    scripts = '  <script src="/js/article.js"></script>'
    if draft:
        head = "\n".join([
            '  <meta name="robots" content="noindex, nofollow, noarchive">',
            '  <meta property="og:locale" content="fa_IR">',
            '  <meta property="og:type" content="article">',
            '  <meta property="og:site_name" content="دکتر نادر اکبری">',
            f'  <meta property="og:title" content="{esc(p.title)}">',
            f'  <meta property="og:description" content="{esc(p.description)}">',
            f'  <meta property="og:url" content="{abs_url(p.draft_path)}">',
            f'  <meta property="og:image" content="{esc(image)}">',
            '  <meta property="og:image:width" content="1200">',
            '  <meta property="og:image:height" content="630">',
            '  <meta name="twitter:card" content="summary_large_image">',
        ])
        schema, analytics = "", ""
        banner = ('  <div class="draft-banner">پیش‌نویس، هنوز منتشر نشده | '
                  '<a href="#review" data-open-review>ثبت تأیید یا نظر دکتر</a></div>')
        scripts += '\n  <script src="/js/review.js"></script>'
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
            '  <meta property="og:image:width" content="1200">',
            '  <meta property="og:image:height" content="630">',
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
        banner = ""

    body_class = "is-draft" if draft else "is-article"
    if p.slug == "دستورالعمل":
        body_class += " has-instr-dl"
    return layout(page_title, p.description, head, schema, analytics, main, banner, scripts,
                  hub_live, p.draft_path if draft else p.path, body_class, pages)


def layout(title, description, head, schema, analytics, main, banner, scripts, hub_live, current, body_class, pages=()):
    header, footer = site_chrome(current, hub_live, pages, bool(analytics))
    return fill(tpl("layout.html"), title=esc(title), description=esc(description), head=head,
                schema=schema, analytics=analytics, main=main, banner=banner, scripts=scripts,
                site_header=header, site_footer=footer, body_class=body_class)


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


def render_hub(pages):
    live = [p for p in pages if p.live]
    live.sort(key=lambda p: (0 if p.type == "pillar" else 1, -(p.updated or p.published or dt.date.min).toordinal()))
    cats = sorted({page_category(p) for p in live})
    filters = ('          <button type="button" class="blog-filter is-active" data-filter="all">همه</button>\n' +
               "\n".join(f'          <button type="button" class="blog-filter" data-filter="{esc(c)}">{esc(c)}</button>'
                         for c in cats))
    cards = "\n".join(hub_card(p) for p in live)
    url = abs_url(f"/{HUB_DIR}/")
    page_title = f"بلاگ آموزشی گوش، حلق و بینی | {DOCTOR}"
    desc = ("مقالات و راهنمای بیماران درباره سینوزیت، جراحی آندوسکوپی سینوس، شستشوی بینی و سایر "
            "موضوعات گوش و حلق و بینی؛ بازبینی‌شده توسط دکتر نادر اکبری دیلمقانی.")
    head = "\n".join([
        f'  <link rel="canonical" href="{url}">',
        '  <meta name="robots" content="index, follow, max-image-preview:large">',
        '  <meta property="og:locale" content="fa_IR">',
        '  <meta property="og:type" content="website">',
        f'  <meta property="og:title" content="{esc(page_title)}">',
        f'  <meta property="og:description" content="{esc(desc)}">',
        f'  <meta property="og:url" content="{url}">',
        f'  <meta property="og:image" content="{DEFAULT_IMAGE}">',
    ])
    items = [{"@type": "ListItem", "position": i + 1, "url": abs_url(p.path), "name": p.title}
             for i, p in enumerate(live)]
    schema = json_ld({"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "@id": url + "#page", "url": url, "name": "بلاگ دکتر نادر اکبری",
         "description": desc, "inLanguage": "fa-IR", "isPartOf": {"@id": SITE + "/#website"},
         "mainEntity": {"@type": "ItemList", "itemListElement": items}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "خانه", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "بلاگ"}]},
    ]})
    main = fill(tpl("hub.html"), filters=filters, cards=cards, count=fa(len(live)))
    scripts = '  <script src="/js/blog.js" defer></script>\n'
    return layout(page_title, desc, head, schema, ANALYTICS, main, "", scripts, True,
                  f"/{HUB_DIR}/", "is-blog", pages)


def render_publications(pages, hub_live):
    data = load_publications_bundle()
    stats = data.get("stats", {}) if data else {}
    pubs = (data or {}).get("publications") or []
    url = abs_url(f"/{PUB_DIR}/")
    pub_og = SITE + "/images/articles/publications/og.jpg"
    page_title = "مقالات علمی دکتر نادر اکبری | جراح بینی و راینولوژیست"
    desc = (
        "مقالات علمی دکتر نادر اکبری دیلمقانی، جراح بینی و فلوشیپ راینولوژی: "
        f"{stats.get('total', len(pubs))} مقاله با آمار استناد از Google Scholar. "
        "جستجو، فیلتر سال و موضوع، مرتب‌سازی بر اساس تاریخ و استناد."
    )
    og_alt = "مقالات علمی دکتر نادر اکبری دیلمقانی — جراح بینی و راینولوژیست"
    head = "\n".join([
        f'  <link rel="canonical" href="{url}">',
        '  <meta name="robots" content="index, follow, max-image-preview:large">',
        '  <meta property="og:locale" content="fa_IR">',
        '  <meta property="og:type" content="website">',
        '  <meta property="og:site_name" content="دکتر نادر اکبری">',
        f'  <meta property="og:title" content="{esc(page_title)}">',
        f'  <meta property="og:description" content="{esc(desc)}">',
        f'  <meta property="og:url" content="{url}">',
        f'  <meta property="og:image" content="{pub_og}">',
        f'  <meta property="og:image:width" content="1200">',
        f'  <meta property="og:image:height" content="630">',
        f'  <meta property="og:image:alt" content="{esc(og_alt)}">',
        '  <meta name="twitter:card" content="summary_large_image">',
        f'  <meta name="twitter:title" content="{esc(page_title)}">',
        f'  <meta name="twitter:description" content="{esc(desc)}">',
        f'  <meta name="twitter:image" content="{pub_og}">',
        f'  <meta name="twitter:image:alt" content="{esc(og_alt)}">',
    ])
    list_items = []
    for i, p in enumerate(pubs[:30]):
        article = {"@type": "ScholarlyArticle", "name": p.get("title"), "url": p.get("url")}
        if p.get("authors"):
            article["author"] = p.get("authors")
        if p.get("year"):
            article["datePublished"] = str(p.get("year"))
        if p.get("journal"):
            article["isPartOf"] = p.get("journal")
        list_items.append({"@type": "ListItem", "position": i + 1, "item": article})
    schema = json_ld({"@context": "https://schema.org", "@graph": [
        {"@type": "CollectionPage", "@id": url + "#page", "url": url,
         "name": "مقالات علمی دکتر نادر اکبری دیلمقانی",
         "description": desc, "inLanguage": "fa-IR", "isPartOf": {"@id": SITE + "/#website"},
         "image": {"@type": "ImageObject", "url": pub_og, "width": 1200, "height": 630},
         "mainEntity": {"@type": "ItemList", "numberOfItems": stats.get("total", len(pubs)),
                        "itemListElement": list_items}},
        {"@type": "Person", "@id": DOCTOR_ID, "name": DOCTOR, "url": SITE + "/",
         "jobTitle": "جراح بینی و فلوشیپ راینولوژی",
         "sameAs": [stats.get("scholarUrl") or SCHOLAR_URL]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "خانه", "item": SITE + "/"},
            {"@type": "ListItem", "position": 2, "name": "مقالات علمی"}]},
    ]})
    main = tpl("publications.html")
    scripts = '  <script src="/js/publications.js" defer></script>\n'
    return layout(page_title, desc, head, schema, ANALYTICS, main, "", scripts, hub_live,
                  f"/{PUB_DIR}/", "is-publications", pages)


def render_sitemap(pages, hub_live):
    rows = [(path, prio, None) for path, prio in STATIC_PAGES]
    live = [p for p in pages if p.live]
    if hub_live:
        rows.append((f"/{HUB_DIR}/", "0.7", max(p.updated for p in live)))
    pub = load_publications_bundle()
    if pub and pub.get("publications"):
        updated = as_date(pub.get("updated")) or dt.date.today()
        rows.append((f"/{PUB_DIR}/", "0.75", updated))
    vids = load_videos()
    if vids:
        dates = [as_date(v.get("date")) for v in vids]
        dates = [d for d in dates if d]
        rows.append((f"/{VIDEO_DIR}/", "0.8", max(dates) if dates else dt.date.today()))
        for v in vids:
            rows.append((f"/{VIDEO_DIR}/{v['slug']}/", "0.65", as_date(v.get("date"))))
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
    hub_live = any(p.live for p in pages)
    apply_static_chrome(hub_live, pages)
    outputs = {}
    pub_live = publications_live()
    known = {"/", f"/{HUB_DIR}/"} | {p.path for p in pages if p.live} | {p.draft_path for p in pages if not p.live}
    if pub_live:
        known.add(f"/{PUB_DIR}/")
    videos = load_videos()
    if videos:
        known.add(f"/{VIDEO_DIR}/")
        known.update(f"/{VIDEO_DIR}/{v['slug']}/" for v in videos)

    for p in pages:
        if p.live:
            outputs[f"{p.slug}/index.html"] = render_page(p, pages, False, hub_live)
            if p.token:
                outputs[f"{DRAFT_DIR}/{p.token}/index.html"] = redirect_page(p.path)
        else:
            outputs[f"{DRAFT_DIR}/{p.token}/index.html"] = render_page(p, pages, True, hub_live)
    if hub_live:
        outputs[f"{HUB_DIR}/index.html"] = render_hub(pages)
        outputs[f"{HUB_LEGACY}/index.html"] = redirect_page(f"/{HUB_DIR}/")
    if pub_live:
        outputs[f"{PUB_DIR}/index.html"] = render_publications(pages, hub_live)
    outputs.update(render_video_pages(pages, hub_live))
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
