"""Brand infographics + hero logo cleanup for week-2 drafts.

Matches published article graphics (IRANYekanX, teal cards, footer logo).
"""
from __future__ import annotations

from pathlib import Path

import arabic_reshaper
from bidi.algorithm import get_display
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
FONT_SRC = ROOT / "fonts"
FONT_CACHE = Path(r"C:\Users\aleca\AppData\Local\Temp\akbari-fonts")
LOGO = ROOT / "images" / "logo-full.png"

INK = (18, 40, 48)
INK_SOFT = (61, 85, 96)
MUTED = (94, 116, 128)
LINE = (215, 228, 234)
BG = (244, 248, 250)
WHITE = (255, 255, 255)
TEAL = (43, 122, 142)
TEAL_DARK = (24, 84, 104)
TEAL_DEEP = (14, 54, 68)
TEAL_SOFT = (229, 243, 247)
GOLD = (194, 120, 58)
GOLD_SOFT = (255, 247, 237)
DANGER = (180, 83, 9)

W = 1200
PAD = 64
PERSIAN_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")


def rtl(text: str) -> str:
    return get_display(arabic_reshaper.reshape(text))


def ensure_fonts() -> dict[str, Path]:
    FONT_CACHE.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}
    mapping = {
        "regular": "IRANYekanX-Regular.woff2",
        "medium": "IRANYekanX-Medium.woff2",
        "bold": "IRANYekanX-Bold.woff2",
        "extrabold": "IRANYekanX-ExtraBold.woff2",
    }
    for key, name in mapping.items():
        ttf = FONT_CACHE / name.replace(".woff2", ".ttf")
        if not ttf.exists() or ttf.stat().st_size < 1000:
            font = TTFont(str(FONT_SRC / name))
            font.flavor = None
            font.save(str(ttf))
        out[key] = ttf
    return out


FONTS = ensure_fonts()


def font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS[weight]), size)


def fa_num(n: int | str) -> str:
    return str(n).translate(PERSIAN_DIGITS)


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.FreeTypeFont, max_w: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if draw.textlength(rtl(trial), font=fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_rtl(draw: ImageDraw.ImageDraw, text: str, xy: tuple[float, float], fnt, fill, anchor="ra"):
    draw.text(xy, rtl(text), font=fnt, fill=fill, anchor=anchor)


def rounded_shadow(base: Image.Image, box: tuple[int, int, int, int], radius=22, blur=10):
    x0, y0, x1, y1 = box
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle((x0 + 4, y0 + 8, x1 + 4, y1 + 10), radius, fill=(14, 54, 68, 28))
    layer = layer.filter(ImageFilter.GaussianBlur(blur))
    out = base.convert("RGBA")
    out.alpha_composite(layer)
    return out.convert("RGB")


def new_canvas(height: int) -> Image.Image:
    img = Image.new("RGB", (W, height), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, W, 8), fill=TEAL)
    draw.ellipse((920, -180, 1320, 220), fill=(232, 243, 246))
    draw.ellipse((-220, height - 260, 180, height + 80), fill=(232, 243, 246))
    return img


def footer(img: Image.Image, y: int) -> None:
    draw = ImageDraw.Draw(img)
    draw.line((PAD, y, W - PAD, y), fill=LINE, width=1)
    draw_rtl(draw, "drnaderakbari.com", (PAD + 220, y + 48), font(22, "medium"), MUTED, anchor="lm")
    logo = Image.open(LOGO).convert("RGBA")
    tw = 280
    ratio = tw / logo.width
    logo = logo.resize((tw, int(logo.height * ratio)), Image.Resampling.LANCZOS)
    img.paste(logo, (W - PAD - logo.width, y + 18), logo)


def header_block(draw, kicker: str, title: str, y: int = 48) -> int:
    draw_rtl(draw, kicker, (W - PAD, y), font(26, "bold"), TEAL)
    y += 46
    f_title = font(42, "extrabold")
    for line in wrap(draw, title, f_title, W - PAD * 2):
        draw_rtl(draw, line, (W - PAD, y), f_title, TEAL_DEEP)
        y += 56
    return y + 18


def card(img: Image.Image, box, fill=WHITE, outline=LINE, radius=22):
    shadowed = rounded_shadow(img, box, radius=radius)
    img.paste(shadowed)
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(box, radius, fill=fill, outline=outline, width=1)
    return img


def number_badge(draw, cx: int, cy: int, n: int, fill=TEAL):
    r = 28
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill)
    draw.text((cx, cy), rtl(fa_num(n)), font=font(22, "extrabold"), fill=WHITE, anchor="mm")


def timeline(path: Path, kicker: str, title: str, steps: list[dict], warning: str | None = None):
    """steps: title, body, optional badge, optional gold."""
    # estimate height
    probe = Image.new("RGB", (W, 200), BG)
    d0 = ImageDraw.Draw(probe)
    f_body = font(24, "regular")
    heights = []
    for step in steps:
        lines = wrap(d0, step["body"], f_body, 760)
        h = 86 + len(lines) * 36
        if step.get("badge"):
            h += 8
        heights.append(max(h, 132))
    warn_h = 118 if warning else 0
    H = 48 + 120 + sum(heights) + 16 * (len(steps) - 1) + warn_h + 150
    img = new_canvas(H)
    draw = ImageDraw.Draw(img)
    y = header_block(draw, kicker, title)

    num_x = W - PAD - 28
    line_top = y + 20
    line_bot = y + sum(heights) + 16 * (len(steps) - 1) - 20
    draw.line((num_x, line_top, num_x, line_bot), fill=(197, 220, 227), width=4)

    for i, step in enumerate(steps, 1):
        h = heights[i - 1]
        gold = bool(step.get("gold"))
        box = (PAD, y, W - PAD - 56, y + h)
        img = card(img, box, fill=GOLD_SOFT if gold else WHITE)
        draw = ImageDraw.Draw(img)
        number_badge(draw, num_x, y + 40, i, GOLD if gold else TEAL)
        draw_rtl(draw, step["title"], (W - PAD - 108, y + 28), font(28, "extrabold"), TEAL_DEEP)
        by = y + 74
        if step.get("badge"):
            bw = int(draw.textlength(rtl(step["badge"]), font=font(16, "bold"))) + 28
            bx0 = PAD + 22
            bx1 = bx0 + bw
            draw.rounded_rectangle((bx0, y + 28, bx1, y + 56), 10, fill=(214, 232, 238) if not gold else (255, 237, 213))
            draw_rtl(draw, step["badge"], (bx1 - 14, y + 42), font(16, "bold"), TEAL_DARK if not gold else GOLD, anchor="rm")
        for line in wrap(draw, step["body"], f_body, 760):
            draw_rtl(draw, line, (W - PAD - 108, by), f_body, INK_SOFT)
            by += 36
        y += h + 16

    if warning:
        box = (PAD, y, W - PAD, y + 96)
        img = card(img, box, fill=GOLD_SOFT, outline=(237, 201, 166))
        draw = ImageDraw.Draw(img)
        for j, line in enumerate(wrap(draw, warning, font(24, "bold"), W - PAD * 2 - 40)):
            draw_rtl(draw, line, (W - PAD - 28, y + 28 + j * 34), font(24, "bold"), DANGER)
        y += 112

    footer(img, y + 8)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "WEBP", quality=90, method=6)
    print("wrote", path, img.size)


def icon_drop(draw, cx, cy, color=TEAL):
    draw.polygon([(cx, cy - 22), (cx + 16, cy + 6), (cx, cy + 22), (cx - 16, cy + 6)], outline=color, width=3)
    draw.arc((cx - 16, cy - 2, cx + 16, cy + 22), 0, 180, fill=color, width=3)


def icon_blocked(draw, cx, cy, color=TEAL):
    draw.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), outline=color, width=3)
    draw.line((cx - 12, cy - 12, cx + 12, cy + 12), fill=color, width=3)


def icon_smell(draw, cx, cy, color=TEAL):
    for i, dy in enumerate((-10, 0, 10)):
        draw.arc((cx - 18, cy + dy - 10, cx + 18, cy + dy + 10), 200, 340, fill=color, width=3)


def icon_face(draw, cx, cy, color=TEAL):
    draw.ellipse((cx - 20, cy - 20, cx + 20, cy + 20), outline=color, width=3)
    draw.ellipse((cx - 8, cy - 6, cx - 4, cy - 2), fill=color)
    draw.ellipse((cx + 4, cy - 6, cx + 8, cy - 2), fill=color)
    draw.arc((cx - 10, cy + 4, cx + 10, cy + 16), 200, 340, fill=color, width=3)


def grid_cards(path: Path, kicker: str, title: str, items: list[dict], takeaway: str, icons):
    H = 1320
    img = new_canvas(H)
    draw = ImageDraw.Draw(img)
    y = header_block(draw, kicker, title)
    gap = 22
    col_w = (W - PAD * 2 - gap) // 2
    row_h = 340
    positions = [
        (PAD + col_w + gap, y),
        (PAD, y),
        (PAD + col_w + gap, y + row_h + gap),
        (PAD, y + row_h + gap),
    ]
    f_body = font(22, "regular")
    for item, icon_fn, (x, top) in zip(items, icons, positions):
        box = (x, top, x + col_w, top + row_h)
        img = card(img, box)
        draw = ImageDraw.Draw(img)
        cx, cy = x + col_w // 2, top + 78
        icon_fn(draw, cx, cy)
        draw_rtl(draw, item["title"], (x + col_w / 2, top + 130), font(26, "extrabold"), TEAL_DEEP, anchor="ma")
        ty = top + 178
        for line in wrap(draw, item["body"], f_body, col_w - 56):
            draw_rtl(draw, line, (x + col_w / 2, ty), f_body, INK_SOFT, anchor="ma")
            ty += 34

    take_y = y + 2 * (row_h + gap) + 18
    box = (PAD, take_y, W - PAD, take_y + 150)
    img = card(img, box, fill=TEAL_DEEP, outline=TEAL_DEEP)
    draw = ImageDraw.Draw(img)
    f_take = font(26, "bold")
    lines = wrap(draw, takeaway, f_take, W - PAD * 2 - 48)
    ty = take_y + 36
    for line in lines:
        draw_rtl(draw, line, (W // 2 + 20, ty), f_take, WHITE, anchor="ma")
        ty += 38
    footer(img, take_y + 178)
    img = img.crop((0, 0, W, take_y + 178 + 96))
    img.save(path, "WEBP", quality=90, method=6)
    print("wrote", path, img.size)


def compare_table(path: Path, kicker: str, title: str, rows: list[tuple[str, str, str]]):
    row_h = 148
    H = 220 + len(rows) * (row_h + 16) + 180
    img = new_canvas(H)
    draw = ImageDraw.Draw(img)
    y = header_block(draw, kicker, title)
    label_w = 150
    col_w = (W - PAD * 2 - label_w - 24) // 2
    # headers: واقعیت (right of pair in LTR coords = left visually? RTL: right column is first)
    # Visual RTL: [مزمن] [حاد] [label] as in reference — right column is first topic.
    # We'll put واقعیت on the right (teal), تبلیغ on the left (gold).
    hx = PAD + col_w + 12
    draw.rounded_rectangle((hx, y, hx + col_w, y + 56), 16, fill=TEAL)
    draw.rounded_rectangle((PAD, y, PAD + col_w, y + 56), 16, fill=GOLD)
    draw_rtl(draw, "واقعیت", (hx + col_w / 2, y + 28), font(24, "extrabold"), WHITE, anchor="mm")
    draw_rtl(draw, "تبلیغ", (PAD + col_w / 2, y + 28), font(24, "extrabold"), WHITE, anchor="mm")
    y += 76
    f_body = font(22, "regular")
    f_lab = font(22, "extrabold")
    for label, myth, fact in rows:
        lab_box = (W - PAD - label_w, y, W - PAD, y + row_h)
        img = card(img, lab_box, fill=TEAL_SOFT, outline=TEAL_SOFT)
        fact_box = (hx, y, hx + col_w, y + row_h)
        myth_box = (PAD, y, PAD + col_w, y + row_h)
        img = card(img, fact_box)
        img = card(img, myth_box)
        draw = ImageDraw.Draw(img)
        draw_rtl(draw, label, (W - PAD - label_w / 2, y + row_h / 2), f_lab, TEAL_DEEP, anchor="mm")
        ty = y + 28
        for line in wrap(draw, fact, f_body, col_w - 40):
            draw_rtl(draw, line, (hx + col_w - 20, ty), f_body, INK)
            ty += 32
        ty = y + 28
        for line in wrap(draw, myth, f_body, col_w - 40):
            draw_rtl(draw, line, (PAD + col_w - 20, ty), f_body, INK)
            ty += 32
        y += row_h + 16
    footer(img, y + 10)
    img.save(path, "WEBP", quality=90, method=6)
    print("wrote", path, img.size)


def rounded_plate(size: tuple[int, int], radius=18, fill=(255, 255, 255, 236)) -> Image.Image:
    plate = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(plate).rounded_rectangle((0, 0, size[0] - 1, size[1] - 1), radius, fill=fill)
    return plate


def replace_hero_badge(im: Image.Image) -> Image.Image:
    """Cover old sharp badge + leftover AI mark with one rounded brand plate."""
    im = im.convert("RGBA")
    plate_w, plate_h = 418, 168
    x, y = 24, im.height - plate_h - 10
    plate = rounded_plate((plate_w, plate_h), radius=20, fill=(255, 255, 255, 248))
    logo = Image.open(LOGO).convert("RGBA")
    target_w = 372
    logo = logo.resize((target_w, int(logo.height * target_w / logo.width)), Image.Resampling.LANCZOS)
    lx = (plate_w - logo.width) // 2
    ly = (plate_h - logo.height) // 2 - 2
    plate.paste(logo, (lx, ly), logo)
    im.alpha_composite(plate, (x, y))
    return im.convert("RGB")


def save_hero_og(hero: Image.Image, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    hero = hero.resize((1200, 675), Image.Resampling.LANCZOS)
    hero.save(dest / "hero.webp", "WEBP", quality=86, method=6)
    og = hero.crop((0, 22, 1200, 652)).resize((1200, 630), Image.Resampling.LANCZOS)
    og.save(dest / "og.jpg", "JPEG", quality=88, optimize=True, progressive=True)
    og.save(dest / "og.webp", "WEBP", quality=86, method=6)
    print("hero/og", dest)


def main() -> None:
    # Infographics
    grid_cards(
        ROOT / "images/articles/nasal-polyps/symptoms.webp",
        "پولیپ بینی",
        "چهار علامت شایع پولیپ بینی",
        [
            {"title": "گرفتگی بینی", "body": "انسداد یک یا هر دو طرف، تنفس دهانی، خروپف و خواب بد."},
            {"title": "کاهش بویایی", "body": "کم شدن یا از بین رفتن حس بویایی و به‌دنبال آن چشایی."},
            {"title": "ترشح پشت حلق", "body": "ترشح غلیظ از جلو یا پشت حلق و صاف کردن مکرر گلو."},
            {"title": "فشار صورت", "body": "سنگینی روی گونه‌ها، بین چشم‌ها یا پیشانی؛ درد شدید کمتر دیده می‌شود."},
        ],
        "اگر دو علامت یا بیشتر، بیش از ۱۲ هفته ادامه داشته باشد، احتمال پولیپ و سینوزیت مزمن مطرح است.",
        [icon_blocked, icon_smell, icon_drop, icon_face],
    )
    timeline(
        ROOT / "images/articles/nasal-polyps/treatment-path.webp",
        "پولیپ بینی",
        "مسیر درمان پولیپ بینی",
        [
            {"title": "ویزیت و آندوسکوپی", "body": "شرح حال، معاینه داخل بینی با آندوسکوپ در مطب و در صورت نیاز سی‌تی‌اسکن سینوس."},
            {"title": "درمان دارویی", "badge": "چند هفته", "body": "شستشوی منظم، اسپری کورتون با تکنیک درست و در صورت نیاز دوره کوتاه قرص کورتون."},
            {"title": "جراحی آندوسکوپی", "badge": "در موارد مقاوم", "gold": True, "body": "اگر پولیپ مسیر تنفس یا سینوس را بسته باشد و دارو کافی نباشد، جراحی از راه بینی مطرح می‌شود."},
            {"title": "مراقبت برای کم کردن برگشت", "body": "ادامه شستشو، اسپری و کنترل آسم یا آلرژی؛ پولیپ بیماری التهابی است و پیگیری لازم دارد."},
        ],
    )
    timeline(
        ROOT / "images/articles/sinus-surgery-when/checklist.webp",
        "سینوزیت و جراحی",
        "چه زمانی جراحی سینوس مطرح می‌شود؟",
        [
            {"title": "شکست درمان کامل", "badge": "بیش از ۱۲ هفته", "body": "شستشو و اسپری کورتون به‌طور منظم استفاده شده و گرفتگی، ترشح یا کاهش بویایی هنوز زندگی را مختل می‌کند."},
            {"title": "پولیپ مسدودکننده", "body": "پولیپ مسیر تنفس یا تخلیه سینوس را بسته و به دارو کوچک نشده است."},
            {"title": "حملات مکرر", "body": "چند دوره سینوزیت در سال که هر بار آنتی‌بیوتیک می‌خواهد."},
            {"title": "مشکل ساختمانی", "body": "انحراف شدید تیغه، بزرگی شاخک یا موکوسل که تهویه سینوس را غیرممکن کرده است."},
            {"title": "علائم هشدار", "gold": True, "body": "تورم چشم، دوبینی، کاهش بینایی، تب با درد شدید پیشانی یا شک به گسترش عفونت؛ این موارد اورژانس‌اند."},
        ],
        "تصمیم با علائم به‌علاوه آندوسکوپی و سی‌تی‌اسکن گرفته می‌شود، نه فقط یک عکس.",
    )
    compare_table(
        ROOT / "images/articles/sinus-laser/compare.webp",
        "عمل سینوس با لیزر",
        "تبلیغ لیزر در برابر واقعیت جراحی",
        [
            ("ابزار اصلی", "لیزر جای عمل سینوس را می‌گیرد", "آندوسکوپ ابزار استاندارد است، نه لیزر"),
            ("پولیپ", "لیزر پولیپ را کامل برمی‌دارد", "پولیپ عمقی سینوس با لیزر خارج نمی‌شود"),
            ("نام عمل", "روش جدید و بدون جراحی", "بسیاری از تبلیغات، همان جراحی آندوسکوپی است"),
            ("انتخاب روش", "بر اساس نام دستگاه", "بر اساس نوع بیماری و آناتومی بینی"),
        ],
    )
    timeline(
        ROOT / "images/articles/postop-instructions/care-map.webp",
        "مراقبت بعد از عمل",
        "سه دستورالعمل اصلی مطب",
        [
            {"title": "سینوس و پولیپ", "body": "شستشوی منظم، پرهیز از فین محکم، سر بالاتر هنگام خواب و ویزیت تمیزکاری داخل بینی."},
            {"title": "هیپوفیز و قاعده جمجمه", "body": "فین، زور زدن و خم شدن شدید ممنوع است. ترشح آبکی یک‌طرفه یا سردرد شدید را فوری گزارش دهید."},
            {"title": "لوزه و لوزه سوم", "body": "غذای نرم و خنک، مایعات کافی. تب بالا یا خونریزی روشن را جدی بگیرید."},
        ],
        "اگر خونریزی روشن و مداوم، تنگی نفس، تب بالا یا تورم چشم داشتید، همان روز با مطب یا اورژانس تماس بگیرید.",
    )

    # Replace leftover AI clinic marks with a single rounded brand plate
    for folder in ("sinus-surgery-when", "postop-instructions"):
        dest = ROOT / "images" / "articles" / folder
        hero = Image.open(dest / "hero.webp")
        save_hero_og(replace_hero_badge(hero), dest)


if __name__ == "__main__":
    main()
