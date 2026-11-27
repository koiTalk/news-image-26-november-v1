"""News image: Thursday 26 November 2026 (complete full day).

Writes one 1024x1024 PNG to $MAKEFUN_OUTPUT_DIR/entry.png (default /output).
Pure standard library: PNG encoder via zlib, 5x7 bitmap font, no network.
All stories are from NEWS_26NOV.md, first reported 26 Nov 2026.
"""
import os
import struct
import zlib

W, H = 1024, 1024

# 5x7 bitmap font, uppercase + digits + punctuation only.
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01110", "10001", "10000", "10000", "10000", "10001", "01110"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01110", "10001", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["01110", "00100", "00100", "00100", "00100", "00100", "01110"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ",": ["00000", "00000", "00000", "00000", "01100", "00100", "01000"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    "-": ["00000", "00000", "00000", "01110", "00000", "00000", "00000"],
    "/": ["00001", "00010", "00010", "00100", "01000", "01000", "10000"],
    "%": ["11001", "11010", "00010", "00100", "01000", "01011", "10011"],
    "(": ["00010", "00100", "01000", "01000", "01000", "00100", "00010"],
    ")": ["01000", "00100", "00010", "00010", "00010", "00100", "01000"],
    "'": ["00100", "00100", "01000", "00000", "00000", "00000", "00000"],
    "+": ["00000", "00100", "00100", "11111", "00100", "00100", "00000"],
    "=": ["00000", "00000", "11111", "00000", "11111", "00000", "00000"],
    "$": ["00100", "01111", "10100", "01110", "00101", "11110", "00100"],
    "!": ["00100", "00100", "00100", "00100", "00100", "00000", "00100"],
    "?": ["01110", "10001", "00001", "00110", "00100", "00000", "00100"],
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def wrap(text, scale, max_w):
    words = text.split(" ")
    lines, cur = [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


class Canvas:
    def __init__(self):
        self.px = bytearray(b"\xf7\xf3\xe8" * (W * H))

    def set(self, x, y, color):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            self.px[i:i + 3] = bytes(color)

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def circle(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def ring(self, cx, cy, r, color, thick=3):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - thick) ** 2 <= d <= r * r:
                    self.set(xx, yy, color)

    def line(self, x0, y0, x1, y1, color):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def poly(self, pts, color):
        # Scanline fill for a simple polygon.
        ys = [p[1] for p in pts]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                for x in range(int(xs[i]), int(xs[i + 1]) + 1):
                    self.set(x, y, color)

    def text(self, x, y, s, scale, color):
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(7):
                for col in range(5):
                    if glyph[row][col] == "1":
                        for dy in range(scale):
                            for dx in range(scale):
                                self.set(cx + col * scale + dx,
                                         y + row * scale + dy, color)
            cx += 6 * scale
        return cx

    def para(self, x, y, s, scale, color, max_w, leading=None):
        if leading is None:
            leading = 9 * scale
        for line in wrap(s, scale, max_w):
            self.text(x, y, line, scale, color)
            y += leading
        return y


NAVY = (20, 33, 61)
WHITE = (255, 255, 255)
RED = (178, 34, 34)
TEAL = (0, 110, 110)
GOLD = (184, 134, 11)
INK = (30, 30, 30)
GREY = (90, 90, 90)
SEA = (198, 224, 240)
LAND = (127, 176, 105)
CARD = (255, 255, 255)
BLUE = (30, 80, 160)


def lonlat(lon, lat):
    # Map area x 24..1000, y 132..298.
    return int(24 + (lon + 180) / 360 * 976), int(132 + (75 - lat) / 130 * 166)


def draw():
    c = Canvas()
    # Header.
    c.rect(0, 0, W, 118, NAVY)
    c.rect(0, 118, W, 4, RED)
    c.text(32, 20, "WORLD NEWS", 6, WHITE)
    c.text(32, 74, "THURSDAY 26 NOVEMBER 2026", 3, (255, 210, 90))
    c.text(700, 26, "FULL DAY", 2, WHITE)
    c.text(700, 50, "34 STORIES TODAY", 2, (200, 210, 230))
    c.text(700, 74, "12 SHOWN HERE", 2, (200, 210, 230))

    # World map strip.
    c.rect(24, 132, 976, 166, SEA)
    continents = [
        [(-168, 66), (-140, 70), (-120, 71), (-100, 72), (-85, 70), (-70, 68),
         (-60, 55), (-65, 45), (-75, 35), (-80, 28), (-90, 20), (-100, 18),
         (-110, 28), (-120, 38), (-125, 48), (-150, 60)],
        [(-80, 10), (-60, 0), (-40, -10), (-35, -20), (-50, -35), (-70, -40),
         (-75, -20), (-80, 0)],
        [(-10, 36), (-5, 48), (0, 58), (10, 60), (20, 58), (28, 55),
         (28, 45), (20, 40), (10, 38), (0, 36)],
        [(-17, 15), (-10, 30), (10, 35), (30, 32), (35, 20), (40, 10),
         (50, 0), (40, -20), (30, -35), (15, -30), (10, -5), (0, 5)],
        [(35, 68), (60, 72), (90, 75), (120, 74), (150, 70), (170, 65),
         (160, 55), (140, 45), (130, 35), (120, 20), (105, 10), (100, 8),
         (95, 15), (85, 8), (75, 20), (65, 25), (55, 30), (45, 40)],
        [(113, -22), (130, -12), (142, -10), (150, -20), (153, -30),
         (140, -38), (130, -32), (115, -35)],
    ]
    for cont in continents:
        c.poly([lonlat(lon, lat) for lon, lat in cont], LAND)
    pins = [
        (47, 29, "1 KUWAIT", 8, -14),
        (4, 51, "2 BRUSSELS", -100, -14),
        (107, -6, "5 BOGOR", -30, 12),
        (-74, 41, "6 NEW YORK", -110, -14),
        (100, 14, "8 BANGKOK", -20, 12),
    ]
    for lon, lat, label, dx, dy in pins:
        x, y = lonlat(lon, lat)
        c.circle(x, y, 7, RED)
        c.circle(x, y, 3, WHITE)
        c.text(x + dx, y + dy, label, 1, NAVY)

    # Lead stories: three columns.
    leads = [
        (RED, "1 - KUWAIT",
         "IRANIAN DRONE ATTACK IN KUWAIT KILLS TWO ITALIANS",
         "TWO RHEINMETALL TECHNICIANS DIE AT AN AIR-DEFENCE STATION. ITALY CONFIRMS THE DEATHS, IRAN DENIES RESPONSIBILITY.",
         "REUTERS / BBC"),
        (BLUE, "2 - EUROPE",
         "EU SUMMIT ENDS WITH NO DEAL ON BUDGET OR UKRAINE LOAN",
         "24 STATES BACK A 45BN LOAN FOR KYIV, BUT LEADERS FAIL TO AGREE THE 1.58 TRILLION BUDGET. TALKS RESUME IN DECEMBER.",
         "CONSILIUM / AP"),
        (TEAL, "3 - CHIPS",
         "NVIDIA HALTS CHIP SHIPMENTS TO SOUTHEAST ASIA",
         "FT REPORTS US EXPORT CONTROLS STOP SERVERS TO MALAYSIA, SINGAPORE, THAILAND AND INDONESIA. DELL AND SUPERMICRO TOLD BUYERS ORDERS WILL NOT SHIP.",
         "REUTERS / FT"),
    ]
    for i, (accent, kicker, head, body, source) in enumerate(leads):
        x = 24 + i * 332
        c.rect(x, 316, 312, 330, CARD)
        c.rect(x, 316, 312, 6, accent)
        # Icon: atom / chip / stars.
        if i == 0:
            c.ring(x + 40, 380, 22, accent, 4)
            c.circle(x + 40, 380, 7, accent)
            c.ring(x + 40, 380, 34, accent, 2)
        elif i == 1:
            c.rect(x + 18, 358, 44, 44, accent)
            c.rect(x + 30, 370, 20, 20, WHITE)
            for k in range(3):
                c.rect(x + 24 + k * 14, 350, 4, 8, accent)
                c.rect(x + 24 + k * 14, 402, 4, 8, accent)
        else:
            c.circle(x + 40, 380, 26, accent)
            for k in range(8):
                import math
                a = k * 3.14159 / 4
                c.circle(x + 40 + int(17 * math.cos(a)),
                         380 + int(17 * math.sin(a)), 2, GOLD)
        c.text(x + 78, 352, kicker, 2, accent)
        c.text(x + 78, 376, "26 NOV 2026", 2, GREY)
        y = c.para(x + 18, 424, head, 2, INK, 276, leading=18)
        y = c.para(x + 18, y + 8, body, 2, GREY, 276, leading=18)
        c.rect(x + 18, 622, 276, 2, accent)
        c.text(x + 18, 630, "SOURCE: " + source, 1, GREY)

    # Also today.
    c.text(24, 664, "ALSO TODAY", 3, NAVY)
    c.rect(24, 692, 976, 3, NAVY)
    items = [
        ("4", "KIM ORDERS WIDER TACTICAL NUCLEAR DEPLOYMENT IN NORTH KOREA"),
        ("5", "INDONESIA MINE TOLL RISES TO 13 DEAD, 13 STILL TRAPPED IN BOGOR"),
        ("6", "THANKSGIVING STORM: NEARLY 1M WITHOUT POWER ON US EAST COAST"),
        ("7", "US APPROVES SPACEX PLAN FOR ONE MILLION SATELLITES"),
        ("8", "BANGKOK REFINERY EXPLOSION INJURES NINE, THREE CRITICALLY"),
        ("9", "UK NET MIGRATION FALLS TO 77,000, LOWEST SINCE 1997"),
        ("10", "GUINEA-BISSAU DELAYS ELECTIONS BY ABOUT TWO YEARS"),
        ("11", "ZELENSKY: US TOO FOCUSED ON MIDDLE EAST, NOT RUSSIA"),
        ("12", "NORSE ATLANTIC SUSPENDS ALL FLIGHTS, WARNS OF BANKRUPTCY"),
    ]
    for j, (num, txt) in enumerate(items):
        col = j % 2
        row = j // 2
        x = 24 + col * 500
        y = 708 + row * 48
        c.circle(x + 12, y + 8, 14, NAVY)
        c.text(x + 10, y + 2, num, 1, WHITE) if len(num) == 1 else c.text(x + 7, y + 2, num, 1, WHITE)
        c.para(x + 30, y, txt, 2, INK, 440, leading=18)

    # Footer.
    c.rect(0, 968, W, 56, NAVY)
    c.text(24, 982, "ALL STORIES FIRST REPORTED 26 NOV 2026", 2, WHITE)
    c.text(24, 1004, "SOURCES: REUTERS, AP, BBC, FT, NWS", 2, (200, 210, 230))
    return c.px


def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def main():
    px = draw()
    raw = bytearray()
    stride = W * 3
    for y in range(H):
        raw.append(0)
        raw.extend(px[y * stride:(y + 1) * stride])
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(png)


if __name__ == "__main__":
    main()
