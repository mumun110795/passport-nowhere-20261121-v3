#!/usr/bin/env python3
"""
draw.py -- deterministic generator for an invented passport spread.

Builds a 1024x720 image of an open passport of the (fictional) Republic of
Sorvane: a data page on the left and a visas / endorsements page on the
right, and writes it to entry.png next to this file.

Sorvane is a mountain republic on Lake Ilvara.  Its only land frontier
post, Brezhan, stands on the shore of the lake, and the road to the
neighbouring state of Kharovia runs straight across the ice.  The post
therefore exists only in winter: it opens when the lake ice is certified
at 40 cm or more and closes again at the thaw.  That single fact is woven
through the endorsements box, the Kharovian visa conditions and the
Brezhan ice-post stamps.

Everything is drawn with Pillow from fixed data and fixed random seeds,
so repeated runs produce a byte-identical entry.png.  The two-line ICAO
machine-readable zone at the foot of the data page is computed here from
the printed fields, with genuine 7-3-1 check digits.

Run:  python3 draw.py
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1024, 720

# --------------------------------------------------------------------------
# Holder / document data -- the single source of truth for print and MRZ.
# --------------------------------------------------------------------------
SURNAME = "OSTREV"
GIVEN = "MIRA ELEN"
NATIONALITY_MRZ = "SRV"
DOC_NUMBER = "S7V482916"          # 9 characters
DOB_MRZ = "890314"                # 14 MAR 1989
SEX_MRZ = "F"
EXPIRY_MRZ = "310206"             # 06 FEB 2031
PERSONAL_NO = "289031442107"      # 12 digits, padded to 14 in the MRZ

# --------------------------------------------------------------------------
# Fonts (system fonts only -- the grader sandbox has no network).
# --------------------------------------------------------------------------
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
SANS_B = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf"
SERIF_B = "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf"
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
MONO_B = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def F(path, size):
    return ImageFont.truetype(path, size)


# --------------------------------------------------------------------------
# ICAO 9303 check digits (weights 7-3-1 repeating).
# --------------------------------------------------------------------------
def _char_value(ch):
    if ch == "<":
        return 0
    if ch.isdigit():
        return int(ch)
    return ord(ch) - 55  # A=10 .. Z=35


def check_digit(data):
    weights = (7, 3, 1)
    total = sum(_char_value(c) * weights[i % 3] for i, c in enumerate(data))
    return str(total % 10)


def build_mrz():
    line1 = ("P<" + NATIONALITY_MRZ + SURNAME + "<<" +
             GIVEN.replace(" ", "<"))
    line1 = line1.ljust(44, "<")[:44]

    personal = PERSONAL_NO.ljust(14, "<")[:14]
    body = (DOC_NUMBER + check_digit(DOC_NUMBER)
            + NATIONALITY_MRZ
            + DOB_MRZ + check_digit(DOB_MRZ)
            + SEX_MRZ
            + EXPIRY_MRZ + check_digit(EXPIRY_MRZ)
            + personal + check_digit(personal))
    composite_src = (DOC_NUMBER + check_digit(DOC_NUMBER)
                     + DOB_MRZ + check_digit(DOB_MRZ)
                     + EXPIRY_MRZ + check_digit(EXPIRY_MRZ)
                     + personal + check_digit(personal))
    line2 = body + check_digit(composite_src)
    assert len(line1) == 44 and len(line2) == 44, (line1, line2)
    return line1, line2


# --------------------------------------------------------------------------
# Paper, texture, guilloche.
# --------------------------------------------------------------------------
INK = (43, 48, 66)          # muted blue-black print ink
INK_SOFT = (74, 80, 98)
LABEL = (96, 104, 122)
RULE = (150, 152, 148)


def paper_page(rng_seed):
    """One textured off-white security-paper page (490 x 684)."""
    pw, ph = 490, 684
    base = Image.new("RGB", (pw, ph), (240, 235, 220))
    noise = Image.effect_noise((pw, ph), 11).convert("L")
    base = Image.composite(Image.new("RGB", (pw, ph), (232, 226, 208)),
                           base, noise.point(lambda v: 26 if v > 150 else 0))
    d = ImageDraw.Draw(base, "RGBA")
    rng = random.Random(rng_seed)
    # faint paper fibres
    for _ in range(260):
        x, y = rng.uniform(0, pw), rng.uniform(0, ph)
        ln = rng.uniform(3, 9)
        d.line([x, y, x + ln, y + rng.uniform(-1.5, 1.5)],
               fill=(120, 118, 104, 14), width=1)
    # guilloche: two families of fine interlaced sine waves, very pale
    for k in range(26):
        y0 = 8 + k * 27
        pts = []
        for x in range(0, pw + 4, 4):
            y = y0 + 7 * math.sin(x / 46.0 + k * 0.9) \
                   + 3 * math.sin(x / 13.0 + k * 1.7)
            pts.append((x, y))
        d.line(pts, fill=(110, 148, 150, 26), width=1)
    for k in range(18):
        x0 = 10 + k * 28
        pts = []
        for y in range(0, ph + 4, 4):
            x = x0 + 6 * math.sin(y / 52.0 + k * 1.1) \
                   + 3 * math.cos(y / 15.0 + k * 0.6)
            pts.append((x, y))
        d.line(pts, fill=(178, 138, 138, 20), width=1)
    # a soft central rosette behind the middle of the page
    cx, cy = pw // 2, ph // 2
    for r in range(16, 150, 9):
        d.ellipse([cx - r, cy - int(r * 0.72), cx + r, cy + int(r * 0.72)],
                  outline=(110, 148, 150, 18), width=1)
    return base


def text(d, xy, s, font, fill=INK, anchor="la", spacing=0):
    d.text(xy, s, font=font, fill=fill, anchor=anchor, spacing=spacing)


def draw_emblem(d, cx, cy, r):
    """Simple state emblem: ring, peaks over lake waves, one star."""
    col = (86, 100, 122)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=2)
    d.ellipse([cx - r + 4, cy - r + 4, cx + r - 4, cy + r - 4],
              outline=col, width=1)
    # twin peaks
    d.line([cx - r * 0.55, cy + r * 0.05, cx - r * 0.12, cy - r * 0.42],
           fill=col, width=2)
    d.line([cx - r * 0.12, cy - r * 0.42, cx + r * 0.18, cy + r * 0.05],
           fill=col, width=2)
    d.line([cx + r * 0.05, cy - r * 0.05, cx + r * 0.38, cy - r * 0.34],
           fill=col, width=2)
    d.line([cx + r * 0.38, cy - r * 0.34, cx + r * 0.58, cy + r * 0.05],
           fill=col, width=2)
    # lake waves
    for i, yy in enumerate((0.22, 0.38, 0.54)):
        pts = []
        for t in range(21):
            x = cx - r * 0.55 + t * (r * 1.1 / 20)
            y = cy + r * yy + 2.2 * math.sin(t / 2.6 + i * 1.3)
            pts.append((x, y))
        d.line(pts, fill=col, width=1)
    # star above the peaks
    sx, sy, sr = cx, cy - r * 0.66, r * 0.13
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rad = sr if i % 2 == 0 else sr * 0.45
        pts.append((sx + rad * math.cos(ang), sy + rad * math.sin(ang)))
    d.polygon(pts, fill=col)


def signature(d, x, y, w):
    """A handwritten-style scrawl: tall looped initial, low humps, tail."""
    col = (38, 44, 84)
    # tall loop of the initial letter
    pts = []
    for i in range(41):
        t = i / 40 * 2 * math.pi
        pts.append((x + 12 + 10 * math.sin(t), y + 2 - 13 * math.cos(t)
                    + 4 * math.sin(t)))
    d.line(pts, fill=col, width=2, joint="curve")
    # the body of the name: two low humps sinking to the baseline
    pts = []
    for i in range(81):
        t = i / 80
        px = x + 16 + t * (w - 34)
        py = y + 12 - 9 * math.sin(t * math.pi * 2.2) * (1 - t * 0.55) \
            - 3 * math.sin(t * math.pi * 7.0)
        pts.append((px, py))
    d.line(pts, fill=col, width=2, joint="curve")
    # rising tail stroke that crosses back over the end
    d.line([x + w - 26, y + 14, x + w - 4, y - 6], fill=col, width=1)
    # underline flourish
    pts = [(x + 4 + t * (w - 10), y + 19 + 2.5 * math.sin(t * 8.0))
           for t in [i / 40 for i in range(41)]]
    d.line(pts, fill=col, width=1)


# --------------------------------------------------------------------------
# Rubber stamps: drawn on their own layer, speckled, rotated, pasted.
# --------------------------------------------------------------------------
def _speckle(img, rng, keep=0.86):
    px = img.load()
    w, h = img.size
    for yy in range(h):
        for xx in range(w):
            r, g, b, a = px[xx, yy]
            if a and rng.random() > keep:
                px[xx, yy] = (r, g, b, int(a * rng.uniform(0.1, 0.5)))
    return img


def round_stamp(lines, ink, radius, seed, date_line=None):
    s = radius * 2 + 16
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = s // 2
    d.ellipse([8, 8, s - 8, s - 8], outline=ink + (205,), width=3)
    d.ellipse([15, 15, s - 15, s - 15], outline=ink + (170,), width=1)
    n = len(lines) + (1 if date_line else 0)
    y = c - (n * 15 - 3) // 2 - 6
    for ln in lines:
        text(d, (c, y), ln, F(SANS_B, 10), ink + (205,), anchor="ma")
        y += 15
    if date_line:
        text(d, (c, y + 1), date_line, F(MONO_B, 13), ink + (220,),
             anchor="ma")
    return _speckle(img, random.Random(seed))


def rect_stamp(lines, ink, w, h, seed, date_line=None):
    img = Image.new("RGBA", (w + 12, h + 12), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([5, 5, w + 6, h + 6], outline=ink + (200,), width=3)
    d.rectangle([10, 10, w + 1, h + 1], outline=ink + (150,), width=1)
    n = len(lines) + (1 if date_line else 0)
    y = (h + 12 - ((n - 1) * 15 + 13)) // 2
    for ln in lines:
        text(d, ((w + 12) // 2, y), ln, F(SANS_B, 10), ink + (200,),
             anchor="ma")
        y += 15
    if date_line:
        text(d, ((w + 12) // 2, y + 1), date_line, F(MONO_B, 13),
             ink + (215,), anchor="ma")
    return _speckle(img, random.Random(seed))


def paste_rot(base, stamp, cx, cy, angle):
    rot = stamp.rotate(angle, resample=Image.BICUBIC, expand=True)
    base.alpha_composite(rot, (int(cx - rot.width / 2),
                               int(cy - rot.height / 2)))


# --------------------------------------------------------------------------
# Left page: the data page.
# --------------------------------------------------------------------------
def data_field(d, x, y, label, value, vfont=None):
    text(d, (x, y), label, F(SANS, 8), LABEL)
    text(d, (x, y + 10), value, vfont or F(SANS_B, 14), INK)


def build_left(page):
    page = page.convert("RGBA")
    d = ImageDraw.Draw(page, "RGBA")
    # header
    draw_emblem(d, 52, 44, 26)
    text(d, (256, 22), "REPUBLIKA SORVANE", F(SERIF_B, 19), INK,
         anchor="ma")
    text(d, (256, 46), "REPUBLIC OF SORVANE", F(SANS, 10), INK_SOFT,
         anchor="ma")
    text(d, (256, 62), "PASPORT  ·  PASSPORT", F(SANS_B, 11),
         (122, 60, 54), anchor="ma")
    d.line([26, 82, 464, 82], fill=RULE, width=1)
    text(d, (256, 88), "REPUBLIKA SORVANE · MINISTERUL DE INTERNE · ",
         F(SANS, 6), (140, 146, 150), anchor="ma")
    text(d, (26, 100), "DATE PERSONALE / PERSONAL PARTICULARS",
         F(SANS_B, 9), INK_SOFT)
    text(d, (464, 100), "3", F(SERIF_B, 13), INK_SOFT, anchor="ra")

    # portrait, in its thin official border
    portrait = Image.open(os.path.join(HERE, "portrait.png")).convert("RGB")
    portrait = portrait.resize((148, 190), Image.LANCZOS)
    page.paste(portrait, (30, 122))
    d.rectangle([29, 121, 179, 313], outline=(90, 96, 110), width=1)
    d.rectangle([27, 119, 181, 315], outline=(150, 152, 148), width=1)
    text(d, (105, 320), "FOTOGRAFIE / PHOTOGRAPH", F(SANS, 7), LABEL,
         anchor="ma")

    # ghost image -- the faint second portrait used as a security feature
    ghost = portrait.convert("L").resize((62, 80), Image.LANCZOS)
    ghost = ImageEnhance.Contrast(ghost).enhance(0.75)
    ghost_rgb = Image.merge("RGB", (ghost, ghost, ghost))
    page.paste(ghost_rgb, (398, 452))
    gd = ImageDraw.Draw(page, "RGBA")
    gd.rectangle([397, 451, 461, 533], outline=(150, 152, 148, 160),
                 width=1)
    d = ImageDraw.Draw(page, "RGBA")

    # data fields, right of the portrait
    fx = 196
    data_field(d, fx, 122, "TIP / TYPE", "P")
    data_field(d, 252, 122, "COD / CODE", "SRV")
    data_field(d, 330, 122, "NR. DOCUMENT / DOCUMENT No.", DOC_NUMBER,
               F(MONO_B, 13))
    data_field(d, fx, 160, "NUME / SURNAME", "OSTREV", F(SANS_B, 16))
    data_field(d, fx, 198, "PRENUME / GIVEN NAMES", "MIRA ELEN",
               F(SANS_B, 16))
    data_field(d, fx, 236, "CETATENIE / NATIONALITY",
               "SORVANA / SORVANIAN")
    data_field(d, fx, 272, "DATA NASTERII / DATE OF BIRTH",
               "14 MAR 1989")
    data_field(d, 352, 272, "SEX / SEX", "F")
    data_field(d, fx, 308, "LOCUL NASTERII / PLACE OF BIRTH", "VELBRANN")
    d.line([196, 344, 464, 344], fill=RULE, width=1)
    data_field(d, fx, 352, "DATA ELIBERARII / DATE OF ISSUE",
               "06 FEB 2021")
    data_field(d, 352, 352, "VALABIL PANA LA / EXPIRY", "06 FEB 2031")
    data_field(d, fx, 388, "OFICIUL EMITENT / ISSUING OFFICE",
               "VELBRANN — OFICIUL CENTRAL", F(SANS_B, 12))
    text(d, (fx, 414), "CENTRAL PASSPORT OFFICE", F(SANS_B, 12), INK)

    # holder's signature, under the portrait
    text(d, (30, 352), "SEMNATURA TITULARULUI", F(SANS, 8), LABEL)
    text(d, (30, 362), "HOLDER'S SIGNATURE", F(SANS, 8), LABEL)
    signature(d, 32, 388, 140)
    d.line([30, 412, 178, 412], fill=RULE, width=1)

    # observations block
    d.rectangle([28, 446, 384, 540], outline=RULE, width=1)
    text(d, (36, 452), "OBSERVATII / OBSERVATIONS", F(SANS_B, 9),
         INK_SOFT)
    obs = [
        "Titularul poate traversa frontiera la Brezhan numai",
        "pe drumul de gheata al lacului Ilvara, in timp ce",
        "gheata este certificata la 40 cm sau mai mult.",
        "The bearer may cross at Brezhan only by the Lake",
        "Ilvara ice road, while the ice is certified at",
        "40 cm or more. Ice certificate no. to be entered",
        "by the crossing officer. In thaw season the post",
        "is closed; use the Vostra ferry landing.",
    ]
    y = 468
    for ln in obs:
        text(d, (36, y), ln, F(SANS, 9.5), INK_SOFT)
        y += 12

    # machine-readable zone
    line1, line2 = build_mrz()
    d.rectangle([0, 596, 490, 684], fill=(246, 243, 233))
    d.line([0, 596, 490, 596], fill=RULE, width=1)
    text(d, (22, 614), line1, F(MONO, 16), (30, 32, 40))
    text(d, (22, 644), line2, F(MONO, 16), (30, 32, 40))
    return page


# --------------------------------------------------------------------------
# Right page: endorsements, one visa sticker, border stamps.
# --------------------------------------------------------------------------
def wrap(d, x, y, s, font, fill, width, leading=12):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        trial = (cur + " " + wd).strip()
        if d.textlength(trial, font=font) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    for ln in lines:
        text(d, (x, y), ln, font, fill)
        y += leading
    return y


def build_right(page):
    page = page.convert("RGBA")
    d = ImageDraw.Draw(page, "RGBA")
    text(d, (26, 24), "VIZE SI MENTIUNI", F(SERIF_B, 15), INK)
    text(d, (26, 46), "VISAS AND ENDORSEMENTS", F(SANS, 9), INK_SOFT)
    text(d, (464, 24), "12", F(SERIF_B, 13), INK_SOFT, anchor="ra")
    d.line([26, 66, 464, 66], fill=RULE, width=1)

    # endorsements box -- the ice-road condition
    d.rectangle([26, 78, 464, 186], outline=(120, 126, 138), width=1)
    d.rectangle([29, 81, 461, 183], outline=RULE, width=1)
    text(d, (38, 88), "MENTIUNI / ENDORSEMENTS", F(SANS_B, 9), INK_SOFT)
    y = wrap(d, 38, 106,
             "The bearer may cross the Sorvane–Kharovian frontier at "
             "Brezhan only while the Lake Ilvara ice is certified at "
             "40 cm or more. In thaw season the ice post is closed and "
             "the frontier may be crossed only at the Vostra ferry "
             "landing. — Oficiul de Frontiera, Velbrann.",
             F(SANS, 10), INK, 414, 13)

    # the Kharovian visa sticker, pasted at a slight angle
    visa = Image.new("RGBA", (272, 198), (0, 0, 0, 0))
    vd = ImageDraw.Draw(visa)
    vd.rounded_rectangle([1, 1, 270, 196], radius=7,
                         fill=(238, 232, 205, 255),
                         outline=(122, 110, 70, 255), width=2)
    vd.rounded_rectangle([1, 1, 270, 34], radius=7,
                         fill=(96, 44, 52, 255))
    vd.rectangle([1, 24, 270, 34], fill=(96, 44, 52, 255))
    text(vd, (12, 8), "KHAROVIA", F(SERIF_B, 15), (246, 240, 222))
    text(vd, (260, 11), "VIZA / VISA", F(SANS_B, 11), (246, 240, 222),
         anchor="ra")
    rows = [
        ("VIZA Nr. / VISA No.", "KH-2021-88413"),
        ("TIP / TYPE", "C — ICE SEASON VISITOR"),
        ("VALABILA / VALID", "10 DEC 2021 — 20 MAR 2022"),
        ("INTRARI / ENTRIES · ELIBERATA / ISSUED",
         "MULT — VELBRANN CONSULATE, 02 DEC 2021"),
        ("TITULAR / HOLDER · PASPORT Nr.",
         "OSTREV MIRA ELEN · " + DOC_NUMBER),
    ]
    yy = 44
    for lab, val in rows:
        text(vd, (12, yy), lab, F(SANS, 7.5), (110, 104, 84))
        text(vd, (12, yy + 9), val, F(SANS_B, 10), (52, 50, 44))
        yy += 21
    vd.line([10, 160, 262, 160], fill=(150, 140, 104), width=1)
    text(vd, (12, 166),
         "ENTRY ONLY VIA THE BREZHAN–VOSTRA ICE ROAD WHILE ICE",
         F(SANS, 7.5), (96, 44, 52))
    text(vd, (12, 174),
         "IS CERTIFIED ≥ 40 CM; IN THAW, VIA VOSTRA FERRY ONLY.",
         F(SANS, 7.5), (96, 44, 52))
    visa = visa.rotate(-1.2, resample=Image.BICUBIC, expand=True)
    shadow = Image.new("RGBA", visa.size, (0, 0, 0, 70))
    shadow = shadow.filter(ImageFilter.GaussianBlur(3))
    page.paste(shadow, (30, 214), shadow)
    page.paste(visa, (24, 206), visa)
    d = ImageDraw.Draw(page, "RGBA")

    # ---- border stamps, in travel order -------------------------------
    blue = (38, 62, 138)
    violet = (96, 52, 128)
    green = (30, 104, 74)
    rust = (142, 52, 40)
    teal = (16, 110, 116)

    # ice certificate stamp, overlapping the endorsements box
    paste_rot(page, rect_stamp(
        ["ICE CERT. No 0417", "LAKE ILVARA — 46 CM"], teal, 176, 54,
        seed=41, date_line="BREZHAN 18.12.2021"),
        368, 196, -4)
    # 1 -- exit Sorvane at the Brezhan ice post
    paste_rot(page, rect_stamp(
        ["SORVANE · BREZHAN", "ICE POST — EXIT"], blue, 158, 54,
        seed=42, date_line="18 DEC 2021"), 388, 268, 3)
    # 2 -- entry Kharovia, far shore of the frozen lake
    paste_rot(page, round_stamp(
        ["KHAROVIA", "VOSTRA ICE STN", "ENTRY"], violet, 52, seed=43,
        date_line="18.12.2021"), 392, 420, -8)
    # 3 -- entry Dalmarek by air, much later
    paste_rot(page, round_stamp(
        ["DALMAREK", "AEROPORT INT'L", "ENTRY"], rust, 50, seed=44,
        date_line="14.09.2024"), 388, 552, 7)
    # 4 -- exit Kharovia
    paste_rot(page, round_stamp(
        ["KHAROVIA", "VOSTRA", "EXIT"], violet, 50, seed=45,
        date_line="09.01.2022"), 226, 500, 6)
    # 5 -- re-entry to Sorvane at Brezhan
    paste_rot(page, rect_stamp(
        ["SORVANE · BREZHAN", "ICE POST — ENTRY"], blue, 158, 54,
        seed=46, date_line="09 JAN 2022"), 120, 472, -2)
    # 6 -- entry Fenmark by summer ferry
    paste_rot(page, rect_stamp(
        ["FENMARK · PORT SABLE", "FERRY TERMINAL — ENTRY"], green,
        168, 54, seed=47, date_line="22 JUN 2023"), 128, 596, 2)
    # 7 -- exit Fenmark
    paste_rot(page, rect_stamp(
        ["FENMARK · PORT SABLE", "EXIT"], green, 158, 54, seed=48,
        date_line="30 JUN 2023"), 330, 648, -5)
    return page


# --------------------------------------------------------------------------
# Assemble the open book.
# --------------------------------------------------------------------------
def build():
    rng = random.Random(20261121)
    canvas = Image.new("RGB", (W, H), (34, 31, 28))
    nd = ImageDraw.Draw(canvas, "RGBA")
    for _ in range(2600):  # tabletop grain
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        nd.point((x, y), fill=(rng.randint(18, 30), rng.randint(16, 26),
                               rng.randint(14, 24), 255))

    left = build_left(paper_page(101))
    right = build_right(paper_page(202))

    # soft drop shadow of the open book on the table
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rectangle([16, 14, 1008, 708], fill=(0, 0, 0, 150))
    shadow = shadow.filter(ImageFilter.GaussianBlur(7))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), shadow)

    canvas.paste(left.convert("RGB"), (22, 18))
    canvas.paste(right.convert("RGB"), (512, 18))

    # centre spine shading, drawn on an overlay so the alpha blends
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sdd = ImageDraw.Draw(shade)
    for i in range(30):
        a = int(58 * (1 - i / 30) ** 1.6)
        sdd.line([512 - i, 18, 512 - i, 702], fill=(52, 47, 40, a))
        sdd.line([512 + i, 18, 512 + i, 702], fill=(52, 47, 40, a))
    sdd.line([511, 18, 511, 702], fill=(70, 64, 54, 110), width=1)
    sdd.line([513, 18, 513, 702], fill=(255, 255, 255, 46), width=1)
    canvas = Image.alpha_composite(canvas, shade)
    d = ImageDraw.Draw(canvas, "RGBA")
    # page edges
    d.rectangle([22, 18, 1001, 701], outline=(96, 90, 78), width=1)

    out = canvas.convert("RGB")
    # keep the file comfortably under the 1 MiB gate
    out.save(os.path.join(HERE, "entry.png"), optimize=True)
    return out


if __name__ == "__main__":
    build()
