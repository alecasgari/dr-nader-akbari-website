"""Week-3 article heroes and infographics, same brand system as week 2."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ASSETS = Path(
    r"C:\Users\aleca\.cursor\projects\c-Users-aleca-OneDrive-Documents-01-Works-26-Dr-Nader-Akbari-Website-dr-nader-akbari-website\assets"
)

spec = importlib.util.spec_from_file_location(
    "week2gfx", ROOT / "scripts" / "generate-week2-graphics.py"
)
gfx = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gfx)


def cover_16_9(im: Image.Image) -> Image.Image:
    im = im.convert("RGB")
    w, h = im.size
    target = 16 / 9
    if w / h > target:
        nw = int(h * target)
        x = (w - nw) // 2
        im = im.crop((x, 0, x + nw, h))
    else:
        nh = int(w / target)
        y = max(0, (h - nh) // 2)
        im = im.crop((0, y, w, y + nh))
    return im.resize((1200, 675), Image.Resampling.LANCZOS)


def save_hero(src: Path, dest: Path) -> None:
    hero = cover_16_9(Image.open(src))
    gfx.save_hero_og(gfx.replace_hero_badge(hero), dest)


def two_col(path: Path, kicker: str, title: str, left_h: str, right_h: str, rows: list[tuple[str, str, str]]):
    row_h = 132
    H = 240 + len(rows) * (row_h + 16) + 180
    img = gfx.new_canvas(H)
    draw = gfx.ImageDraw.Draw(img)
    y = gfx.header_block(draw, kicker, title)
    label_w = 168
    col_w = (gfx.W - gfx.PAD * 2 - label_w - 24) // 2
    hx = gfx.PAD + col_w + 12
    draw.rounded_rectangle((hx, y, hx + col_w, y + 56), 16, fill=gfx.TEAL)
    draw.rounded_rectangle((gfx.PAD, y, gfx.PAD + col_w, y + 56), 16, fill=gfx.GOLD)
    gfx.draw_rtl(draw, right_h, (hx + col_w / 2, y + 28), gfx.font(24, "extrabold"), gfx.WHITE, anchor="mm")
    gfx.draw_rtl(draw, left_h, (gfx.PAD + col_w / 2, y + 28), gfx.font(24, "extrabold"), gfx.WHITE, anchor="mm")
    y += 76
    f_body = gfx.font(22, "regular")
    f_lab = gfx.font(22, "extrabold")
    for label, left, right in rows:
        img = gfx.card(img, (gfx.W - gfx.PAD - label_w, y, gfx.W - gfx.PAD, y + row_h), fill=gfx.TEAL_SOFT, outline=gfx.TEAL_SOFT)
        img = gfx.card(img, (hx, y, hx + col_w, y + row_h))
        img = gfx.card(img, (gfx.PAD, y, gfx.PAD + col_w, y + row_h))
        draw = gfx.ImageDraw.Draw(img)
        gfx.draw_rtl(draw, label, (gfx.W - gfx.PAD - label_w / 2, y + row_h / 2), f_lab, gfx.TEAL_DEEP, anchor="mm")
        ty = y + 22
        for line in gfx.wrap(draw, right, f_body, col_w - 36):
            gfx.draw_rtl(draw, line, (hx + col_w - 18, ty), f_body, gfx.INK)
            ty += 32
        ty = y + 22
        for line in gfx.wrap(draw, left, f_body, col_w - 36):
            gfx.draw_rtl(draw, line, (gfx.PAD + col_w - 18, ty), f_body, gfx.INK)
            ty += 32
        y += row_h + 16
    gfx.footer(img, y + 10)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "WEBP", quality=90, method=6)
    print("wrote", path, img.size)


def main() -> None:
    save_hero(
        ASSETS / "polyp-recurrence-hero-v2.jpg",
        ROOT / "images" / "articles" / "polyp-recurrence",
    )
    save_hero(
        ASSETS / "sinus-bleeding-hero-v2.jpg",
        ROOT / "images" / "articles" / "sinus-bleeding",
    )
    gfx.grid_cards(
        ROOT / "images/articles/polyp-recurrence/who-recurs.webp",
        "برگشت پولیپ",
        "چه کسانی بیشتر در معرض برگشت‌اند؟",
        [
            {"title": "آسم", "body": "التهاب بینی و ریه اغلب هم‌سفرند و عود پولیپ را بیشتر می‌کنند."},
            {"title": "آسپرین", "body": "بدتر شدن با آسپرین یا ضدالتهاب، از بالاترین خطرهای برگشت است."},
            {"title": "قطع اسپری", "body": "بهتر شدن نفس مجوز قطع اسپری نگهدارنده نیست."},
            {"title": "سیگار و دود", "body": "سیگار و قلیان ترمیم مخاط را کند و التهاب را زنده نگه می‌دارند."},
        ],
        "احتمال شما را معاینه تعیین می‌کند، نه یک درصد ثابت در اینترنت.",
        [gfx.icon_smell, gfx.icon_blocked, gfx.icon_drop, gfx.icon_face],
    )
    gfx.timeline(
        ROOT / "images/articles/polyp-recurrence/prevention.webp",
        "بعد از عمل پولیپ",
        "چه کارهایی برگشت را کمتر می‌کند؟",
        [
            {"title": "اسپری را ادامه دهید", "badge": "نگهدارنده", "body": "پاشش به سمت خارج بینی، منظم، حتی وقتی تنفس باز شده است."},
            {"title": "شستشوی سرم", "body": "دلمه را برمی‌دارد تا دارو به مخاط برسد. آب ساده و روغن جایگزین سرم نیستند."},
            {"title": "ویزیت آندوسکوپی", "badge": "زودتر از آینه", "body": "پولیپ کوچک را بیمار در خانه نمی‌بیند. نوبت پیگیری را عقب نیندازید."},
            {"title": "آسم و مسکن", "gold": True, "body": "آسم را همزمان کنترل کنید. آسپرین و ایبوپروفن را اگر حساسیت دارید خودسرانه نخورید."},
        ],
        "جراحی پولیپ را برمی‌دارد؛ اسپری و شستشو راه را باز نگه می‌دارند.",
    )
    two_col(
        ROOT / "images/articles/sinus-bleeding/normal-vs-urgent.webp",
        "بعد از عمل سینوس",
        "خون‌آبه طبیعی یا خونریزی خطرناک؟",
        "خبر دهید",
        "معمولاً طبیعی",
        [
            ("رنگ", "روشن، پیوسته یا جهنده", "صورتی، قهوه‌ای رقیق، لکه روی دستمال"),
            ("مدت", "با ده تا پانزده دقیقه نشستن بند نمی‌آید", "چند روز اول، کم‌حجم و رو به کاهش"),
            ("شستشو", "جریان قرمز خالص وسط سرم", "کمی رنگ صورتی در سرم"),
            ("همراه", "غش، تورم چشم، تب، ترشح آبکی یک‌طرفه", "گرفتگی و مزه خفیف خون در گلو"),
        ],
    )
    gfx.timeline(
        ROOT / "images/articles/sinus-bleeding/timeline.webp",
        "خونریزی بعد از عمل",
        "ترشح خونی را روزبه‌روز بشناسید",
        [
            {"title": "روز اول تا سوم", "body": "خون‌آبه و گرفتگی در اوج است. سر بالاتر، غذای داغ نه، تامپون را بیرون نکشید."},
            {"title": "هفته اول", "badge": "فین ممنوع", "body": "فعالیت سبک آزاد است. عطسه با دهان باز، حمام ولرم، سونا نه."},
            {"title": "حدود روز ۷ تا ۱۰", "gold": True, "body": "دلمه جدا می‌شود. خون تازه اگر بند آمد به مطب بگویید؛ اگر ماند، اورژانس."},
            {"title": "اگر همین حالا خون روشن آمد", "body": "بنشینید، سر کمی جلو، پره نرم بینی را پیوسته فشار دهید. یخ بیرون بینی باشد نه داخل سوراخ."},
        ],
        "ترشح آبکی شفاف یک‌طرفه خون‌آبه نیست؛ همان روز خبر دهید.",
    )


if __name__ == "__main__":
    main()
