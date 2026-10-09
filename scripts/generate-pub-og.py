"""Generate Open Graph image for /مقالات-علمی/ (1200x630) with correct RTL Persian."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
except ImportError:
    raise SystemExit("Install: pip install arabic-reshaper python-bidi pillow")

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "images" / "articles" / "publications"
OUT_JPG = OUT_DIR / "og.jpg"
OUT_WEBP = OUT_DIR / "og.webp"

W, H = 1200, 630
TEAL = (43, 122, 142)
TEAL_DEEP = (14, 54, 68)
TEAL_LIGHT = (229, 243, 247)
WHITE = (255, 255, 255)
MUTED = (200, 220, 228)


def rtl(text: str) -> str:
    return get_display(arabic_reshaper.reshape(text))


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = ["tahomabd.ttf", "tahoma.ttf"] if bold else ["tahoma.ttf", "arial.ttf"]
    root = Path("C:/Windows/Fonts")
    for name in names:
        path = root / name
        if path.is_file():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def wrap_rtl(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        w = draw.textlength(rtl(trial), font=font)
        if w <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_rtl_line(draw: ImageDraw.ImageDraw, text: str, xy: tuple[int, int], font: ImageFont.FreeTypeFont, fill: tuple):
    shaped = rtl(text)
    draw.text(xy, shaped, font=font, fill=fill, anchor="ra")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (W, H), TEAL_LIGHT)
    draw = ImageDraw.Draw(img)

    draw.rectangle((0, H - 220, W, H), fill=TEAL_DEEP)
    draw.rectangle((0, 0, W, 12), fill=TEAL)
    draw.ellipse((880, -120, 1180, 180), fill=(55, 130, 148))
    draw.ellipse((-80, 380, 220, 680), fill=(210, 232, 238))

    margin_r = W - 72
    y = 88
    f_kicker = load_font(26, bold=True)
    f_title = load_font(46, bold=True)
    f_sub = load_font(28)
    f_brand = load_font(24, bold=True)

    draw_rtl_line(draw, "فعالیت‌های پژوهشی", (margin_r, y), f_kicker, TEAL)
    y += 52

    title = "مقالات علمی دکتر نادر اکبری دیلمقانی"
    for line in wrap_rtl(draw, title, f_title, W - 144):
        draw_rtl_line(draw, line, (margin_r, y), f_title, TEAL_DEEP)
        y += 58

    y += 8
    draw_rtl_line(draw, "جراح بینی · راینولوژی · Google Scholar", (margin_r, y), f_sub, (61, 90, 102))
    y += 48

    badge_y = H - 150
    draw.rounded_rectangle((72, badge_y, 420, badge_y + 56), radius=14, fill=TEAL)
    f_url = load_font(22, bold=True)
    draw.text((246, badge_y + 28), "drnaderakbari.com", font=f_url, fill=WHITE, anchor="mm")

    img.save(OUT_JPG, "JPEG", quality=92, optimize=True, progressive=True)
    img.save(OUT_WEBP, "WEBP", quality=90, method=6)
    print(f"Wrote {OUT_JPG} ({OUT_JPG.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
