import sys, os
from PIL import Image, ImageDraw
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
W, H = 1404, 1872
BORDER, GUIDE = 90, 170  # gray levels (0 black .. 255 white)

def dashed(d, p0, p1, fill, dash=8, gap=8, width=2):
    (x0, y0), (x1, y1) = p0, p1
    if x0 == x1:
        y = y0
        while y < y1:
            d.line([(x0, y), (x0, min(y + dash, y1))], fill=fill, width=width); y += dash + gap
    else:
        x = x0
        while x < x1:
            d.line([(x, y0), (min(x + dash, x1), y0)], fill=fill, width=width); x += dash + gap

# (a) kana practice grid: 6 x 8 large squares, centre guide crosses
img = Image.new("L", (W, H), 255); d = ImageDraw.Draw(img)
cell, cols, rows = 216, 6, 8
x0, y0 = (W - cols * cell) // 2, (H - rows * cell) // 2
for r in range(rows):
    for c in range(cols):
        x, y = x0 + c * cell, y0 + r * cell
        dashed(d, (x + cell // 2, y + 6), (x + cell // 2, y + cell - 6), GUIDE)
        dashed(d, (x + 6, y + cell // 2), (x + cell - 6, y + cell // 2), GUIDE)
for i in range(cols + 1):
    d.line([(x0 + i * cell, y0), (x0 + i * cell, y0 + rows * cell)], fill=BORDER, width=3)
for i in range(rows + 1):
    d.line([(x0, y0 + i * cell), (x0 + cols * cell, y0 + i * cell)], fill=BORDER, width=3)
img.save(os.path.join(out, "Kana Grid.png"), optimize=True)

# (b) genko yoshi: 20 x 20 manuscript paper, centre gutter, header space
img = Image.new("L", (W, H), 255); d = ImageDraw.Draw(img)
cell, n = 66, 20
x0, y0 = (W - n * cell) // 2, 300
for i in range(n + 1):
    w = 3 if i in (0, n) else 2
    d.line([(x0 + i * cell, y0), (x0 + i * cell, y0 + n * cell)], fill=BORDER, width=w)
    d.line([(x0, y0 + i * cell), (x0 + n * cell, y0 + i * cell)], fill=BORDER, width=w)
# centre gutter (between columns 10 and 11): double line + tick marks every 5 rows
gx = x0 + (n // 2) * cell
d.line([(gx - 5, y0), (gx - 5, y0 + n * cell)], fill=BORDER, width=2)
d.line([(gx + 5, y0), (gx + 5, y0 + n * cell)], fill=BORDER, width=2)
for k in range(5, n, 5):
    d.line([(x0, y0 + k * cell), (x0 + n * cell, y0 + k * cell)], fill=BORDER, width=4)
# header rule for title / name
d.line([(x0, 200), (x0 + n * cell, 200)], fill=BORDER, width=2)
img.save(os.path.join(out, "Genko Yoshi.png"), optimize=True)
