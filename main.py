#!/usr/bin/env python3
"""news-image-20261119 entry: a one-page newspaper front page summing up the
world news of Thursday 19 November 2026, drawn programmatically and written to
/output/entry.png.

Pure Python 3 standard library (zlib, struct, binascii, os). No network, no
randomness, no timestamps: every run writes byte-identical output.

Design: a newspaper front page. The masthead names the day in large type, the
lead story is the first-ever U.S.-China-Russia trilateral summit in Shenzhen,
and four panels cover the day's other consequential stories across regions and
fields: gold crashing below $3,700 on hawkish Fed minutes, the Houthi missile
strike on Riyadh's PIF Tower, Europe's Ukraine summit in Berlin, and the
U.S.-China trade truce extension. Every story is labelled in short, plain
text so a viewer who missed the day can tell what happened from the image
alone. All text is drawn with an embedded 5x7 pixel font, so it stays crisp
and legible at any size, with no garbled glyphs.
"""

import binascii
import os
import struct
import zlib

W = 1024
H = 1024

# --- Palette -----------------------------------------------------------------
PAPER = (245, 240, 230)   # warm off-white page
INK = (20, 24, 31)        # near-black text
WHITE = (255, 255, 255)
NAVY = (15, 36, 64)       # masthead / footer band
GOLD = (212, 160, 23)     # gold rule, masthead accent
GOLD_DARK = (154, 123, 10)
RED = (169, 50, 38)       # lead kicker, Middle East header
BLUE = (31, 78, 121)      # Europe header
GREEN = (30, 107, 58)     # Trade header
SUB = (58, 58, 58)        # subline grey
LIGHT = (232, 226, 214)   # light text on dark bands
FLAG_RED = (222, 41, 16)  # China flag red
FLAG_BLUE = (60, 59, 110) # US canton blue
RU_BLUE = (0, 57, 166)    # Russia flag blue
STAR_YELLOW = (255, 222, 0)

# --- 5x7 pixel font ----------------------------------------------------------
# Each glyph is 7 rows of 5 bits; bit 4 (0b10000) is the leftmost pixel.
# Uppercase letters, digits and the punctuation this page uses.
FONT = {
    'A': (0b01110, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    'B': (0b11110, 0b10001, 0b10001, 0b11110, 0b10001, 0b10001, 0b11110),
    'C': (0b01110, 0b10001, 0b10000, 0b10000, 0b10000, 0b10001, 0b01110),
    'D': (0b11110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b11110),
    'E': (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b11111),
    'F': (0b11111, 0b10000, 0b10000, 0b11110, 0b10000, 0b10000, 0b10000),
    'G': (0b01110, 0b10001, 0b10000, 0b10111, 0b10001, 0b10001, 0b01111),
    'H': (0b10001, 0b10001, 0b10001, 0b11111, 0b10001, 0b10001, 0b10001),
    'I': (0b01110, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    'J': (0b00111, 0b00010, 0b00010, 0b00010, 0b00010, 0b10010, 0b01100),
    'K': (0b10001, 0b10010, 0b10100, 0b11000, 0b10100, 0b10010, 0b10001),
    'L': (0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b10000, 0b11111),
    'M': (0b10001, 0b11011, 0b10101, 0b10101, 0b10001, 0b10001, 0b10001),
    'N': (0b10001, 0b11001, 0b10101, 0b10011, 0b10001, 0b10001, 0b10001),
    'O': (0b01110, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    'P': (0b11110, 0b10001, 0b10001, 0b11110, 0b10000, 0b10000, 0b10000),
    'Q': (0b01110, 0b10001, 0b10001, 0b10001, 0b10101, 0b10010, 0b01101),
    'R': (0b11110, 0b10001, 0b10001, 0b11110, 0b10100, 0b10010, 0b10001),
    'S': (0b01111, 0b10000, 0b10000, 0b01110, 0b00001, 0b00001, 0b11110),
    'T': (0b11111, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00100),
    'U': (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01110),
    'V': (0b10001, 0b10001, 0b10001, 0b10001, 0b10001, 0b01010, 0b00100),
    'W': (0b10001, 0b10001, 0b10001, 0b10101, 0b10101, 0b10101, 0b01010),
    'X': (0b10001, 0b10001, 0b01010, 0b00100, 0b01010, 0b10001, 0b10001),
    'Y': (0b10001, 0b10001, 0b01010, 0b00100, 0b00100, 0b00100, 0b00100),
    'Z': (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b10000, 0b11111),
    '0': (0b01110, 0b10001, 0b10011, 0b10101, 0b11001, 0b10001, 0b01110),
    '1': (0b00100, 0b01100, 0b00100, 0b00100, 0b00100, 0b00100, 0b01110),
    '2': (0b01110, 0b10001, 0b00001, 0b00110, 0b01000, 0b10000, 0b11111),
    '3': (0b11111, 0b00010, 0b00100, 0b00010, 0b00001, 0b10001, 0b01110),
    '4': (0b00010, 0b00110, 0b01010, 0b10010, 0b11111, 0b00010, 0b00010),
    '5': (0b11111, 0b10000, 0b11110, 0b00001, 0b00001, 0b10001, 0b01110),
    '6': (0b00110, 0b01000, 0b10000, 0b11110, 0b10001, 0b10001, 0b01110),
    '7': (0b11111, 0b00001, 0b00010, 0b00100, 0b01000, 0b01000, 0b01000),
    '8': (0b01110, 0b10001, 0b10001, 0b01110, 0b10001, 0b10001, 0b01110),
    '9': (0b01110, 0b10001, 0b10001, 0b01111, 0b00001, 0b00010, 0b01100),
    ' ': (0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000),
    '.': (0b00000, 0b00000, 0b00000, 0b00000, 0b00000, 0b01100, 0b01100),
    ',': (0b00000, 0b00000, 0b00000, 0b00000, 0b01100, 0b00100, 0b01000),
    ':': (0b00000, 0b01100, 0b01100, 0b00000, 0b01100, 0b01100, 0b00000),
    '-': (0b00000, 0b00000, 0b00000, 0b01110, 0b00000, 0b00000, 0b00000),
    "'": (0b00100, 0b00100, 0b01000, 0b00000, 0b00000, 0b00000, 0b00000),
    '(': (0b00010, 0b00100, 0b01000, 0b01000, 0b01000, 0b00100, 0b00010),
    ')': (0b01000, 0b00100, 0b00010, 0b00010, 0b00010, 0b00100, 0b01000),
    '/': (0b00001, 0b00010, 0b00010, 0b00100, 0b01000, 0b01000, 0b10000),
    '%': (0b11001, 0b11010, 0b00010, 0b00100, 0b01000, 0b01011, 0b10011),
    '$': (0b00100, 0b01111, 0b10100, 0b01110, 0b00101, 0b11110, 0b00100),
    '+': (0b00000, 0b00100, 0b00100, 0b01110, 0b00100, 0b00100, 0b00000),
    '=': (0b00000, 0b00000, 0b11111, 0b00000, 0b11111, 0b00000, 0b00000),
    '!': (0b00100, 0b00100, 0b00100, 0b00100, 0b00100, 0b00000, 0b00100),
    '?': (0b01110, 0b10001, 0b00001, 0b00010, 0b00100, 0b00000, 0b00100),
    '&': (0b01100, 0b10010, 0b10100, 0b01000, 0b10101, 0b10010, 0b01101),
    '"': (0b01010, 0b01010, 0b00000, 0b00000, 0b00000, 0b00000, 0b00000),
    '*': (0b00000, 0b10101, 0b01110, 0b10101, 0b00000, 0b00000, 0b00000),
}
BLANK = FONT[' ']


class Canvas:
    """An RGB framebuffer with the drawing primitives the page needs."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(bytes(bg) * (w * h))

    def _idx(self, x, y):
        return (y * self.w + x) * 3

    def set_px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = self._idx(x, y)
            self.buf[i:i + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = self._idx(x0, yy)
            self.buf[i:i + len(row)] = row

    def rect_border(self, x, y, w, h, color, t=2):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def hline(self, x, y, w, color):
        self.fill_rect(x, y, w, 1, color)

    def line(self, x0, y0, x1, y1, color):
        """Bresenham line."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set_px(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def fill_polygon(self, pts, color):
        """Scanline fill for a simple polygon."""
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.fill_rect(int(xs[i]), y, max(1, int(xs[i + 1]) - int(xs[i])), 1, color)

    def star5(self, cx, cy, r, color):
        """Five-pointed star, one point up."""
        import math
        pts = []
        for i in range(10):
            ang = math.pi * i / 5 - math.pi / 2
            rad = r if i % 2 == 0 else r * 0.42
            pts.append((cx + int(rad * math.cos(ang)), cy + int(rad * math.sin(ang))))
        self.fill_polygon(pts, color)

    # -- text ---------------------------------------------------------------
    def text_width(self, text, scale):
        return (len(text) * 6 - 1) * scale

    def text(self, x, y, s, scale, color):
        cx = x
        for ch in s.upper():
            glyph = FONT.get(ch, BLANK)
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits & (0b10000 >> col):
                        self.fill_rect(cx + col * scale, y + row * scale,
                                       scale, scale, color)
            cx += 6 * scale

    def text_centered(self, cx, y, s, scale, color):
        self.text(cx - self.text_width(s, scale) // 2, y, s, scale, color)


# --- PNG encoding -------------------------------------------------------------

def _chunk(kind, data):
    c = struct.pack(">I", len(data)) + kind + data
    return c + struct.pack(">I", binascii.crc32(kind + data) & 0xFFFFFFFF)


def encode_png(w, h, buf):
    raw = bytearray()
    stride = w * 3
    for y in range(h):
        raw.append(0)  # filter: none
        raw += buf[y * stride:(y + 1) * stride]
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += _chunk(b"IHDR", ihdr)
    png += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += _chunk(b"IEND", b"")
    return png


# --- Flags --------------------------------------------------------------------

def flag_usa(cv, x, y, w, h):
    stripe = h // 13
    for i in range(13):
        if i % 2 == 0:
            cv.fill_rect(x, y + i * stripe, w, stripe + 1, (178, 34, 52))
    canton_w = int(w * 0.4)
    canton_h = stripe * 7
    cv.fill_rect(x, y, canton_w, canton_h, FLAG_BLUE)
    for r in range(5):
        for c in range(6):
            sx = x + 6 + c * (canton_w - 12) // 5
            sy = y + 5 + r * (canton_h - 10) // 4
            cv.fill_rect(sx, sy, 3, 3, WHITE)


def flag_china(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, FLAG_RED)
    cv.star5(x + int(w * 0.28), y + int(h * 0.32), int(h * 0.20), STAR_YELLOW)
    for sx, sy in ((0.55, 0.14), (0.68, 0.26), (0.68, 0.46), (0.55, 0.56)):
        cv.star5(x + int(w * sx), y + int(h * sy), int(h * 0.08), STAR_YELLOW)


def flag_russia(cv, x, y, w, h):
    third = h // 3
    cv.fill_rect(x, y, w, third + 1, WHITE)
    cv.fill_rect(x, y + third, w, third + 1, RU_BLUE)
    cv.fill_rect(x, y + 2 * third, w, h - 2 * third, (213, 0, 50))


# --- Panel icons (drawn in the header strip, right side) -----------------------

def icon_chart(cv, x, y, color):
    # Falling line chart with an arrowhead: gold's drop.
    cv.line(x, y + 4, x + 6, y + 9, color)
    cv.line(x + 6, y + 9, x + 12, y + 7, color)
    cv.line(x + 12, y + 7, x + 20, y + 18, color)
    cv.line(x + 20, y + 18, x + 16, y + 17, color)
    cv.line(x + 20, y + 18, x + 19, y + 13, color)


def icon_tower(cv, x, y, color):
    # Skyscraper with a burst at the top: the Riyadh strike.
    cv.fill_rect(x + 7, y + 5, 8, 17, color)
    cv.fill_rect(x + 9, y + 2, 4, 4, color)
    cv.line(x + 2, y + 2, x + 6, y + 6, color)
    cv.line(x + 20, y + 2, x + 16, y + 6, color)
    cv.line(x + 1, y + 9, x + 6, y + 10, color)
    cv.line(x + 21, y + 9, x + 16, y + 10, color)


def icon_eu(cv, x, y, color):
    # Ring of stars: Europe.
    import math
    for i in range(12):
        ang = 2 * math.pi * i / 12
        cv.fill_rect(x + 11 + int(8 * math.cos(ang)),
                     y + 11 + int(8 * math.sin(ang)), 2, 2, color)


def icon_trade(cv, x, y, color):
    # Two opposing arrows: a trade deal.
    cv.line(x + 2, y + 8, x + 18, y + 8, color)
    cv.line(x + 18, y + 8, x + 14, y + 5, color)
    cv.line(x + 18, y + 8, x + 14, y + 11, color)
    cv.line(x + 20, y + 16, x + 4, y + 16, color)
    cv.line(x + 4, y + 16, x + 8, y + 13, color)
    cv.line(x + 4, y + 16, x + 8, y + 19, color)


# --- Page composition ---------------------------------------------------------

def panel(cv, x, y, w, h, header_color, tag, icon, headline, sublines, fact):
    cv.fill_rect(x, y, w, h, WHITE)
    cv.rect_border(x, y, w, h, INK, 2)
    cv.fill_rect(x + 2, y + 2, w - 4, 34, header_color)
    cv.text(x + 14, y + 11, tag, 3, WHITE)
    icon(cv, x + w - 40, y + 7, WHITE)
    ty = y + 48
    for line in headline:
        cv.text(x + 14, ty, line, 4, INK)
        ty += 34
    ty += 8
    for line in sublines:
        cv.text(x + 14, ty, line, 3, SUB)
        ty += 25
    # A bottom fact line fills the panel and adds one more verified detail.
    cv.hline(x + 14, y + h - 34, w - 28, GOLD)
    cv.text(x + 14, y + h - 28, fact, 2, SUB)


def compose():
    cv = Canvas(W, H, PAPER)

    # Masthead: the day, named large.
    cv.fill_rect(0, 0, W, 118, NAVY)
    cv.text_centered(W // 2, 18, "ONE DAY IN THE WORLD", 3, GOLD)
    cv.text_centered(W // 2, 52, "THURSDAY 19 NOVEMBER 2026", 6, WHITE)
    cv.fill_rect(0, 118, W, 6, GOLD)

    # Lead story: the Shenzhen trilateral.
    lx, ly, lw, lh = 16, 130, 992, 316
    cv.fill_rect(lx, ly, lw, lh, WHITE)
    cv.rect_border(lx, ly, lw, lh, INK, 2)
    cv.text(lx + 16, ly + 14, "SHENZHEN, CHINA - APEC SUMMIT - KYLIN VILLA", 3, RED)
    cv.text(lx + 16, ly + 46, "FIRST U.S.-CHINA-RUSSIA", 6, INK)
    cv.text(lx + 16, ly + 94, "SUMMIT IN HISTORY", 6, INK)
    cv.text(lx + 16, ly + 152, "TRUMP, XI AND PUTIN SIGN A FOUR-POINT", 3, SUB)
    cv.text(lx + 16, ly + 178, "PEACE DECLARATION - NO DEAL ON UKRAINE OR IRAN", 3, SUB)
    fw, fh = 170, 80
    for i, (flag, label) in enumerate((
            (flag_usa, "UNITED STATES"),
            (flag_china, "CHINA"),
            (flag_russia, "RUSSIA"))):
        fx = lx + 76 + i * 351
        flag(cv, fx, ly + 208, fw, fh)
        cv.rect_border(fx, ly + 208, fw, fh, INK, 1)
        cv.text_centered(fx + fw // 2, ly + 292, label, 2, SUB)

    # Four panels: markets, Middle East, Europe, trade.
    panel(cv, 16, 458, 488, 236, GOLD_DARK, "MARKETS", icon_chart,
          ["GOLD CRASHES", "BELOW $3,700"],
          ["LOWEST IN 14 MONTHS",
           "AS FED MINUTES POINT",
           "TO MORE RATE HIKES"],
          "DOWN OVER 30% FROM JANUARY RECORD")
    panel(cv, 520, 458, 488, 236, RED, "MIDDLE EAST", icon_tower,
          ["HOUTHI MISSILE", "HITS RIYADH TOWER"],
          ["PIF TOWER WINDOWS BLOWN",
           "OUT ACROSS SEVEN FLOORS",
           "NO INJURIES REPORTED"],
          "SECOND STRIKE HERE IN TWO WEEKS")
    panel(cv, 16, 706, 488, 236, BLUE, "EUROPE", icon_eu,
          ["EUROPE RALLIES FOR", "UKRAINE IN BERLIN"],
          ["BERLIN SUMMIT BACKS 45BN",
           "EURO UKRAINE LOAN FOR 2027",
           "UK SENDS 1,000+ DRONES"],
          "30+ LEADERS - WITKOFF, KUSHNER ATTEND")
    panel(cv, 520, 706, 488, 236, GREEN, "TRADE", icon_trade,
          ["U.S.-CHINA TRADE", "TRUCE EXTENDED"],
          ["TRUMP AND XI AGREE IN",
           "SHENZHEN - DETAILS NOT",
           "YET ANNOUNCED"],
          "TRUCE HAD BEEN DUE TO END JANUARY 10")

    # Footer band: more of the day, and the date again. Lines are spaced 20px
    # apart for 14px glyphs so they never touch.
    cv.fill_rect(0, 950, W, 74, NAVY)
    cv.text_centered(W // 2, 954,
                     "ALSO: PHILLY FED SURVEY MISSES - DOLLAR NEARS 19-MONTH HIGH",
                     2, LIGHT)
    cv.text_centered(W // 2, 974, "NYT: TRUMP WEIGHS NEW STRIKES ON IRAN", 2, LIGHT)
    cv.text_centered(W // 2, 994, "AS REPORTED ON 19 NOVEMBER 2026", 2, GOLD)

    return cv.buf


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    png = encode_png(W, H, compose())
    with open(os.path.join(out_dir, "entry.png"), "wb") as f:
        f.write(png)


if __name__ == "__main__":
    main()
