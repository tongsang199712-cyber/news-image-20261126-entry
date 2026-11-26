#!/usr/bin/env python3
"""news-image-20261126 -- a newspaper front page summing up the world news
of Thursday 26 November 2026, drawn entirely in code.

Pure Python 3 standard library. The program paints into an RGB pixel
buffer (1024x1024) and hand-encodes a PNG (zlib + CRC, no image library).
Deterministic: the same bytes come out of every run.
"""
import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (246, 241, 227)   # newsprint cream
INK = (26, 26, 26)        # near-black ink
RED = (176, 42, 32)       # masthead red
BLUE = (31, 78, 121)      # section blue
GOLD = (184, 138, 44)     # accent gold
GREY = (120, 112, 96)     # muted rule grey
ORANGE = (214, 106, 24)   # flame orange
GREEN = (46, 110, 62)     # small green accent

buf = bytearray(W * H * 3)


def px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i], buf[i + 1], buf[i + 2] = c


def rect(x, y, w, h, c):
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        for xx in range(x0, x1):
            i = base + (xx - x0) * 3
            buf[i], buf[i + 1], buf[i + 2] = c


def hline(x, y, w, c, t=1):
    rect(x, y, w, t, c)


def vline(x, y, h, c, t=1):
    rect(x, y, t, h, c)


def line(x0, y0, x1, y1, c, t=1):
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    while True:
        rect(x - t // 2, y - t // 2, t, t, c)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy


def circle(cx, cy, r, c, fill=True):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            d = (xx - cx) ** 2 + (yy - cy) ** 2
            if fill:
                if d <= r * r:
                    px(xx, yy, c)
            else:
                if r * r - 2 * r <= d <= r * r:
                    px(xx, yy, c)


def ellipse(cx, cy, rx, ry, c):
    for yy in range(cy - ry, cy + ry + 1):
        for xx in range(cx - rx, cx + rx + 1):
            if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0:
                px(xx, yy, c)


def triangle(x0, y0, x1, y1, x2, y2, c):
    minx, maxx = min(x0, x1, x2), max(x0, x1, x2)
    miny, maxy = min(y0, y1, y2), max(y0, y1, y2)
    d = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if d == 0:
        return
    for yy in range(miny, maxy + 1):
        for xx in range(minx, maxx + 1):
            a = ((y1 - y2) * (xx - x2) + (x2 - x1) * (yy - y2)) / d
            b = ((y2 - y0) * (xx - x2) + (x0 - x2) * (yy - y2)) / d
            cc = 1 - a - b
            if 0 <= a <= 1 and 0 <= b <= 1 and 0 <= cc <= 1:
                px(xx, yy, c)


# ---------------------------------------------------------------- font
# 5x7 bitmap font. Each glyph is 7 rows of 5 bits, '1' = ink.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '@': ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    '[': ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    ']': ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    '<': ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    '>': ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def draw_text(x, y, s, scale, c):
    """Draw text at top-left (x, y); scale multiplies the 5x7 glyphs."""
    cx = x
    for ch in s.upper():
        g = FONT.get(ch, FONT['?'])
        for row in range(7):
            bits = g[row]
            for col in range(5):
                if bits[col] == '1':
                    rect(cx + col * scale, y + row * scale, scale, scale, c)
        cx += 6 * scale
    return cx


def draw_centered(y, s, scale, c, x0=0, x1=W):
    w = text_width(s, scale)
    draw_text(x0 + (x1 - x0 - w) // 2, y, s, scale, c)


def wrap(s, max_w, scale):
    """Greedy word wrap; returns list of lines fitting max_w pixels."""
    words = s.upper().split()
    lines, cur = [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def draw_para(x, y, s, max_w, scale, c, leading=None):
    lh = leading if leading is not None else 9 * scale
    for i, ln in enumerate(wrap(s, max_w, scale)):
        draw_text(x, y + i * lh, ln, scale, c)
    return y + len(wrap(s, max_w, scale)) * lh


# ---------------------------------------------------------------- PNG
def chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def encode_png():
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)  # filter: none
        raw += buf[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


# ---------------------------------------------------------------- icons
# Each icon draws inside a ~96x76 box at (x, y). Simple flat pictograms.

def icon_tariffs(x, y):
    # bar chart with rising bars and a dollar sign, on axes
    rect(x + 8, y + 58, 80, 3, INK)
    rect(x + 8, y + 6, 3, 55, INK)
    bars = [(16, 22, RED), (34, 34, BLUE), (52, 44, GOLD), (70, 54, RED)]
    for bx, bh, bc in bars:
        rect(x + bx, y + 58 - bh, 12, bh, bc)
    line(x + 12, y + 12, x + 84, y + 2, INK, 2)
    triangle(x + 84, y + 2, x + 76, y + 2, x + 84, y + 10, INK)


def icon_jet(x, y):
    # fighter jet seen from above, with a burst behind it
    triangle(x + 78, y + 34, x + 44, y + 22, x + 44, y + 46, BLUE)
    triangle(x + 44, y + 28, x + 18, y + 8, x + 30, y + 34, BLUE)
    triangle(x + 44, y + 40, x + 18, y + 60, x + 30, y + 34, BLUE)
    triangle(x + 52, y + 30, x + 30, y + 16, x + 40, y + 34, BLUE)
    triangle(x + 52, y + 38, x + 30, y + 52, x + 40, y + 34, BLUE)
    # explosion star at the tail
    cx, cy = x + 10, y + 34
    for dx, dy in [(0, -12), (9, -9), (12, 0), (9, 9), (0, 12),
                   (-9, 9), (-12, 0), (-9, -9)]:
        line(cx, cy, cx + dx, cy + dy, ORANGE, 3)
    circle(cx, cy, 5, RED)


def icon_fire(x, y):
    # fuel tanker with flames
    rect(x + 8, y + 34, 52, 22, BLUE)          # tank body
    rect(x + 60, y + 40, 20, 16, INK)          # cab
    rect(x + 68, y + 43, 8, 8, PAPER)          # cab window
    circle(x + 20, y + 58, 6, INK)
    circle(x + 46, y + 58, 6, INK)
    circle(x + 70, y + 58, 6, INK)
    # flames above the tank
    triangle(x + 18, y + 34, x + 26, y + 6, x + 34, y + 34, ORANGE)
    triangle(x + 34, y + 34, x + 44, y + 12, x + 52, y + 34, RED)
    triangle(x + 48, y + 34, x + 56, y + 18, x + 62, y + 34, ORANGE)


def icon_court(x, y):
    # courthouse: pediment, columns, steps, gavel
    triangle(x + 6, y + 8, x + 88, y + 8, x + 47, y + 26, INK)
    rect(x + 10, y + 28, 74, 4, INK)
    for cx in (16, 34, 52, 70):
        rect(x + cx, y + 32, 6, 26, INK)
    rect(x + 8, y + 58, 78, 4, INK)
    rect(x + 4, y + 62, 86, 4, GREY)
    # small gavel resting on the steps
    rect(x + 66, y + 44, 18, 5, RED)
    line(x + 75, y + 49, x + 75, y + 58, RED, 3)


def icon_flag(x, y):
    # Swiss flag on a pole, with an outward arrow (expulsion)
    vline(x + 12, y + 6, 56, INK, 3)
    rect(x + 16, y + 8, 44, 34, RED)
    rect(x + 34, y + 14, 8, 22, PAPER)
    rect(x + 24, y + 19, 28, 8, PAPER)
    line(x + 64, y + 50, x + 88, y + 50, INK, 3)
    triangle(x + 88, y + 50, x + 78, y + 44, x + 78, y + 56, INK)
    draw_text(x + 64, y + 56, "OUT", 1, RED)


def icon_talks(x, y):
    # two speech bubbles facing each other, cracked apart
    ellipse(x + 26, y + 26, 22, 15, BLUE)
    ellipse(x + 68, y + 26, 22, 15, RED)
    triangle(x + 30, y + 38, x + 22, y + 52, x + 38, y + 38, BLUE)
    triangle(x + 64, y + 38, x + 72, y + 52, x + 56, y + 38, RED)
    line(x + 47, y + 8, x + 47, y + 26, INK, 3)
    line(x + 47, y + 26, x + 41, y + 34, INK, 3)
    line(x + 41, y + 34, x + 47, y + 42, INK, 3)
    line(x + 47, y + 42, x + 47, y + 58, INK, 3)
    draw_text(x + 14, y + 60, "NO DEAL", 1, INK)


def icon_balloon(x, y):
    # parade balloon with string, clouds and confetti
    ellipse(x + 47, y + 26, 26, 20, RED)
    triangle(x + 40, y + 44, x + 54, y + 44, x + 47, y + 52, RED)
    line(x + 47, y + 52, x + 47, y + 66, INK, 2)
    ellipse(x + 16, y + 16, 14, 6, BLUE)
    ellipse(x + 78, y + 60, 12, 5, BLUE)
    for bx, by, bc in [(12, 44, GOLD), (84, 22, GOLD), (70, 12, ORANGE),
                       (24, 58, ORANGE)]:
        rect(x + bx, y + by, 4, 4, bc)


def icon_guitar(x, y):
    # electric guitar with music notes
    circle(x + 34, y + 44, 18, RED)
    circle(x + 34, y + 44, 8, PAPER)
    rect(x + 46, y + 18, 34, 8, INK)
    rect(x + 78, y + 14, 8, 16, INK)
    line(x + 30, y + 44, x + 80, y + 22, INK, 2)
    # hand-drawn quaver notes (no font glyph for them)
    circle(x + 70, y + 58, 4, BLUE)
    line(x + 74, y + 58, x + 74, y + 44, BLUE, 2)
    line(x + 74, y + 44, x + 82, y + 48, BLUE, 2)
    circle(x + 14, y + 16, 3, BLUE)
    line(x + 17, y + 16, x + 17, y + 4, BLUE, 2)


# ---------------------------------------------------------------- layout
M = 32            # page margin
CW = W - 2 * M    # content width


def masthead():
    rect(0, 0, W, H, PAPER)
    # top rules
    hline(M, 18, CW, INK, 4)
    draw_centered(30, "THE DAILY WORLD", 5, INK)
    hline(M, 84, CW, INK, 2)
    draw_centered(94, "THURSDAY 26 NOVEMBER 2026", 2, RED)
    hline(M, 118, CW, INK, 4)


def lead_story():
    y = 132
    draw_text(M, y, "TRADE WAR, NEW FRONT", 2, BLUE)
    y += 30
    draw_text(M, y, "U.S. UNVEILS SWEEPING", 3, INK)
    y += 34
    draw_text(M, y, "NEW TARIFFS ON 14", 3, INK)
    y += 34
    draw_text(M, y, "ECONOMIES", 3, INK)
    # body text, left column
    by = 132 + 30 + 34 * 3 + 8
    draw_para(M, by, "Washington proposes levies on China, the EU, "
              "India and 11 more partners.", 560, 2, INK)
    # bar-chart illustration, right side
    icon_tariffs(700, 150)
    draw_text(700, 232, "TARIFFS AIM AT", 1, GREY)
    draw_text(700, 244, "OVER-CAPACITY", 1, GREY)
    hline(M, 316, CW, INK, 3)


def story_cell(x, y, w, h, tag, headline, body, icon):
    rect(x, y, w, h, PAPER)
    rect(x, y, w, h, GREY)  # thin frame via 1px border drawn as outline
    rect(x + 1, y + 1, w - 2, h - 2, PAPER)
    draw_text(x + 12, y + 10, tag, 1, BLUE)
    icon(x + 12, y + 30)
    tx = x + 118
    tw = w - 130
    hy = y + 12
    for ln in wrap(headline, tw, 2):
        draw_text(tx, hy, ln, 2, INK)
        hy += 20
    draw_para(tx, hy + 4, body, tw, 1, INK, leading=11)


def grid():
    # 7 stories in a 2-column grid; last cell is the day-in-brief box
    gx, gy = M, 332
    cw = (CW - 16) // 2
    ch = 152
    cells = [
        ("UKRAINE WAR", "UKRAINE HITS RUSSIAN AIRBASE, FIVE PLANES DAMAGED",
         "Kyiv says its drones struck Savasleyka airbase deep inside Russia.",
         icon_jet),
        ("EGYPT", "CAIRO TANKER FIRE KILLS AT LEAST 31",
         "A fuel tanker overturned and burst into flames on a crowded highway.",
         icon_fire),
        ("ISRAEL", "JUDGES URGE DROPPING TOP NETANYAHU CHARGES",
         "Israeli judges recommend the gravest counts in the PM's trial be dropped.",
         icon_court),
        ("KOREA", "NORTH KOREA EXPELS SWISS DIPLOMAT",
         "Pyongyang orders Switzerland to close its newly opened office.",
         icon_flag),
        ("DIPLOMACY", "ABU DHABI PEACE TALKS END WITHOUT A DEAL",
         "Ukraine-Russia talks stall as Moscow refuses any territorial compromise.",
         icon_talks),
        ("THANKSGIVING", "MACY'S PARADE POSTPONED BY BAD WEATHER",
         "New York delays its Thanksgiving parade as storms sweep the US East Coast.",
         icon_balloon),
        ("MUSIC", "DURAN DURAN GUITARIST ANDY TAYLOR DIES AT 65",
         "The guitarist and songwriter behind the band's biggest hits has died.",
         icon_guitar),
    ]
    for i, (tag, head, body, icon) in enumerate(cells):
        cx = gx + (i % 2) * (cw + 16)
        cy = gy + (i // 2) * (ch + 12)
        story_cell(cx, cy, cw, ch, tag, head, body, icon)
    # day-in-brief box in the 8th cell
    bx = gx + cw + 16
    by = gy + 3 * (ch + 12)
    bw, bh = cw, ch
    rect(bx, by, bw, bh, INK)
    draw_text(bx + 12, by + 10, "THE DAY IN BRIEF", 2, GOLD)
    notes = [
        "US STOCKS SLIDE AS AI SELL-OFF DEEPENS",
        "BIRTHRIGHT CITIZENSHIP ORDER BLOCKED AGAIN",
        "SPAIN OPENS PROBE INTO TIKTOK ABUSE CONTENT",
        "MISS UNIVERSE 2026: PUERTO RICO TAKES CROWN",
    ]
    ny = by + 42
    for n in notes:
        rect(bx + 12, ny + 3, 8, 8, RED)
        draw_para(bx + 28, ny, n, bw - 40, 1, PAPER, leading=11)
        ny += 26
    hline(M, 984, CW, INK, 2)
    draw_centered(990, "THE DAILY WORLD - 26 NOVEMBER 2026 - ALL THE NEWS THAT FITS IN ONE PICTURE", 1, GREY)


def main():
    masthead()
    lead_story()
    grid()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "output"
    os.makedirs(outdir, exist_ok=True)
    data = encode_png()
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {path} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
