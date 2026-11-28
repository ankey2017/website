# -*- coding: utf-8 -*-
"""绘图基元：字体、渐变背景、卡片、富文本（蓝色高亮）、光标、纸张素材"""
import os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, DUR = 1080, 1920, 30, 45.0

NAVY_TOP = (6, 18, 34)
NAVY_MID = (10, 30, 54)
NAVY_BOT = (13, 40, 70)
BLUE = (46, 123, 255)
BLUE_L = (110, 178, 255)
BLUE_D = (24, 74, 160)
WHITE = (246, 249, 255)
MUTED = (152, 172, 198)
DIM = (110, 132, 160)
RED = (255, 104, 104)
AMBER = (255, 190, 92)

FONT_DIR = r"C:\Windows\Fonts"
_fcache = {}


def font(size, weight="r"):
    key = (size, weight)
    if key in _fcache:
        return _fcache[key]
    name = "msyhbd.ttc" if weight == "b" else "msyh.ttc"
    f = ImageFont.truetype(os.path.join(FONT_DIR, name), size)
    _fcache[key] = f
    return f


# ---------------- 缓动 ----------------
def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = clamp(t)
    return 3 * t * t - 2 * t * t * t


def ease_back(t, s=1.7):
    t = clamp(t)
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    return tuple(int(round(lerp(c1[i], c2[i], t))) for i in range(3))


def lerp3(c1, c2, c3, t):
    return lerp_color(c1, c2, t / 0.55) if t < 0.55 else lerp_color(c2, c3, (t - 0.55) / 0.45)


# ---------------- 背景 ----------------
def make_background():
    base = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(base)
    for y in range(H):
        d.line([(0, y), (W, y)], fill=lerp3(NAVY_TOP, NAVY_MID, NAVY_BOT, y / H))

    # 顶部柔光
    glow = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([-260, -680, W + 260, 760], fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(190))
    glow = glow.point(lambda v: int(v * 0.22))
    base = Image.composite(Image.new("RGB", (W, H), (54, 118, 214)), base, glow)

    # 细网格
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdr = ImageDraw.Draw(grid)
    step = 96
    for x in range(0, W, step):
        gdr.line([(x, 0), (x, H)], fill=(120, 170, 240, 9))
    for y in range(0, H, step):
        gdr.line([(0, y), (W, y)], fill=(120, 170, 240, 9))
    base = Image.alpha_composite(base.convert("RGBA"), grid).convert("RGB")

    # 暗角
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-380, -260, W + 380, H + 260], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(240))
    dark = Image.new("RGB", (W, H), (3, 9, 18))
    inv = vig.point(lambda v: int((255 - v) * 0.55))
    base = Image.composite(dark, base, inv)
    return base


def make_scrim(y0=1460, y1=1920, strength=0.62):
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for y in range(y0, y1):
        t = (y - y0) / max(1, (y1 - y0))
        a = int(255 * strength * (t ** 1.5))
        d.line([(0, y), (W, y)], fill=(4, 12, 24, a))
    return ov


# ---------------- 富文本 ----------------
def parse_rich(s):
    out, i = [], 0
    while True:
        a = s.find("[[", i)
        if a < 0:
            if s[i:]:
                out.append((s[i:], False))
            break
        if s[i:a]:
            out.append((s[i:a], False))
        b = s.find("]]", a)
        if b < 0:
            out.append((s[a + 2:], True))
            break
        out.append((s[a + 2:b], True))
        i = b + 2
    return out


def layout_rich(s, size, max_w, weight="b"):
    f = font(size, weight)
    glyphs = []
    for text, hl in parse_rich(s):
        for ch in text:
            if ch == "\n":
                glyphs.append(("\n", hl, 0.0))
            else:
                glyphs.append((ch, hl, f.getlength(ch)))
    lines, cur, cur_w = [], [], 0.0
    for ch, hl, w in glyphs:
        if ch == "\n":
            lines.append(cur)
            cur, cur_w = [], 0.0
            continue
        if cur_w + w > max_w and cur:
            lines.append(cur)
            cur, cur_w = [], 0.0
        cur.append((ch, hl, w))
        cur_w += w
    if cur:
        lines.append(cur)
    return lines, f


def draw_rich(img, s, cy, size, max_w=980, color=WHITE, hl_color=BLUE_L, weight="b",
              align="center", line_gap=1.34, colors=None, shadow=None):
    """在图片上居中绘制一段带蓝色高亮的文字，返回占用高度"""
    lines, f = layout_rich(s, size, max_w, weight)
    lh = int(size * line_gap)
    total = lh * len(lines)
    y = cy - total / 2
    d = ImageDraw.Draw(img)
    for line in lines:
        lw = sum(g[2] for g in line)
        x = (W - lw) / 2 if align == "center" else 64
        for ch, hl, w in line:
            c = hl_color if hl else color
            if colors is not None and not hl:
                c = colors
            if shadow:
                d.text((x + shadow[0], y + shadow[1]), ch, font=f, fill=shadow[2])
            d.text((x, y), ch, font=f, fill=c)
            x += w
        y += lh
    return total


def text_w(s, size, weight="r"):
    return font(size, weight).getlength(s)


def draw_text(img, xy, s, size, color=WHITE, weight="r", anchor="la"):
    ImageDraw.Draw(img).text(xy, s, font=font(size, weight), fill=color, anchor=anchor)


# ---------------- 形状 ----------------
_shadow_cache = {}


def rounded_shadow(w, h, r, blur=30, alpha=120, dy=14):
    key = (w, h, r, blur, alpha, dy)
    if key in _shadow_cache:
        return _shadow_cache[key]
    pad = blur + dy
    im = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([pad, pad + dy, pad + w, pad + h + dy], radius=r, fill=(2, 8, 18, alpha))
    im = im.filter(ImageFilter.GaussianBlur(blur))
    _shadow_cache[key] = im
    return im


def paste_shadow(img, x, y, w, h, r, blur=30, alpha=120, dy=14):
    sh = rounded_shadow(w, h, r, blur, alpha, dy)
    pad = blur + dy
    img.alpha_composite(sh, (int(x - pad), int(y - pad)))


def paste_card(img, x, y, w, h, r=22, fill=(255, 255, 255, 255), shadow=(34, 120, 0.55)):
    if shadow:
        paste_shadow(img, x, y, w, h, r, blur=int(shadow[0]), alpha=int(230 * shadow[2]), dy=int(shadow[1]))
    layer = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=fill)
    img.alpha_composite(layer, (int(x), int(y)))


def paste_rounded(img, im, x, y, w, h, r=18, border=None):
    im = im.convert("RGBA").resize((int(w), int(h)), Image.Resampling.LANCZOS)
    mask = Image.new("L", (int(w), int(h)), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)
    if border:
        bd = ImageDraw.Draw(im)
        bd.rounded_rectangle([0, 0, w - 1, h - 1], radius=r, outline=border, width=2)
    img.paste(im, (int(x), int(y)), mask)


def pill(img, x, y, w, h, text, size=30, fg=WHITE, bg=(255, 255, 255, 26), weight="b", border=None):
    layer = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h / 2, fill=bg, outline=border, width=2 if border else 1)
    ImageDraw.Draw(layer).text((w / 2, h / 2), text, font=font(size, weight), fill=fg, anchor="mm")
    img.alpha_composite(layer, (int(x), int(y)))


# ---------------- 光标 ----------------
CURSOR = [(0, 0), (0, 34), (8, 26), (14, 40), (20, 37), (14, 24), (26, 24)]


def draw_cursor(img, x, y, alpha=255, scale=1.0):
    pts = [(x + px * scale, y + py * scale) for px, py in CURSOR]
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.polygon(pts, fill=(255, 255, 255, alpha))
    d.line(pts + [pts[0]], fill=(18, 40, 70, alpha), width=2)
    img.alpha_composite(layer)


def draw_ripple(img, x, y, p, maxr=64, color=BLUE_L):
    p = clamp(p)
    if p <= 0 or p >= 1:
        return
    r = maxr * ease_out(p)
    a = int(200 * (1 - p) ** 1.6)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([x - r, y - r, x + r, y + r], outline=color + (a,), width=max(2, int(5 * (1 - p))))
    r2 = r * 0.55
    d.ellipse([x - r2, y - r2, x + r2, y + r2], fill=color + (max(0, int(70 * (1 - p))),))
    img.alpha_composite(layer)


def draw_focus(img, x, y, w, h, p, color=BLUE):
    p = clamp(p)
    if p <= 0:
        return
    a = int(200 * ease_out(p))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([x, y, x + w, y + h], radius=10, outline=color + (a,), width=3)
    d.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=color + (int(26 * ease_out(p)),))
    img.alpha_composite(layer)


# ---------------- 纸张素材 ----------------
def _scribble(d, x0, y, wid, rng, color=(58, 72, 96, 205), thick=2, gap_prob=0.12):
    x = x0
    pts = []
    while x < x0 + wid:
        pts.append((x, y + rng.uniform(-1.6, 1.6)))
        x += rng.uniform(2.5, 6.5)
        if rng.random() < gap_prob:
            if len(pts) > 2:
                d.line(pts, fill=color, width=thick, joint="curve")
            x += rng.uniform(6, 14)
            pts = []
    if len(pts) > 2:
        d.line(pts, fill=color, width=thick, joint="curve")


def make_ledger(seed=1, w=820, h=1120, title="收费台账"):
    """手写纸质台账"""
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=6, fill=(250, 248, 242, 255))
    # 表头
    d.rectangle([0, 0, w - 1, 96], fill=(226, 232, 240, 255))
    d.line([(0, 96), (w, 96)], fill=(120, 140, 165, 255), width=2)
    _scribble(d, 26, 44, 190, rng, color=(50, 66, 92, 235), thick=4, gap_prob=0.06)
    d.text((w - 210, 36), "2026 年 10 月", font=font(32, "b"), fill=(70, 86, 110, 255))
    # 表格线
    top = 96
    rows = int((h - top - 30) / 62)
    for i in range(rows + 1):
        y = top + i * 62
        d.line([(0, y), (w, y)], fill=(168, 186, 208, 255), width=1)
    cols = [0, 62, 210, 470, 640, w]
    for cx in cols:
        d.line([(cx, top), (cx, h - 20)], fill=(168, 186, 208, 255), width=1)
    # 内容
    for i in range(rows):
        y = top + i * 62
        d.text((22, y + 16), str(i + 1), font=font(24), fill=(120, 138, 160, 255))
        _scribble(d, 72, y + 31, 120, rng, gap_prob=0.2)
        _scribble(d, 222, y + 31, 230, rng, gap_prob=0.18)
        # 金额
        if rng.random() < 0.8:
            amt = rng.choice(["1,280", "860", "2,400", "1,150", "3,600", "980", "2,050"])
            d.text((480, y + 14), amt, font=font(30, "b"), fill=(40, 60, 90, 255))
        if rng.random() < 0.45:
            d.text((660, y + 14), "欠", font=font(30, "b"), fill=(200, 60, 60, 255))
        elif rng.random() < 0.6:
            d.text((660, y + 14), "√", font=font(30, "b"), fill=(50, 120, 70, 255))
    # 红笔圈注
    for _ in range(2):
        cx, cy = rng.randint(160, w - 200), rng.randint(top + 80, h - 120)
        d.ellipse([cx - 70, cy - 34, cx + 70, cy + 34], outline=(210, 55, 55, 210), width=3)
    return im


def make_excel(seed=2, w=960, h=660):
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=(255, 255, 255, 255))
    header_h = 46
    d.rectangle([0, 0, w - 1, header_h], fill=(33, 115, 70, 255))
    d.text((16, 8), "房屋收费明细 2026-10.xlsx", font=font(26, "b"), fill=(255, 255, 255, 255))
    # 列号
    y0 = header_h
    d.rectangle([0, y0, w - 1, y0 + 34], fill=(240, 243, 246, 255))
    cols = 6
    cw = (w - 46) / cols
    letters = "ABCDEF"
    d.text((10, y0 + 6), " ", font=font(18))
    for i in range(cols):
        d.text((46 + i * cw + 10, y0 + 4), letters[i], font=font(22, "b"), fill=(90, 105, 120, 255))
    # 单元格
    y = y0 + 34
    names = ["张明", "李红", "王强", "赵敏", "陈刚", "刘芳", "周涛", "吴敏", "郑伟", "孙丽", "马超", "胡静", "高强"]
    rooms = ["1-101", "1-102", "2-201", "2-202", "3-301", "3-302", "4-401", "4-402",
             "5-501", "5-502", "6-601", "6-602", "7-701"]
    data = [["房号", "业主", "应收", "实收", "欠费", "状态"]]
    for i in range(len(rooms)):
        due = 1280 if i % 3 == 0 else (960 if i % 3 == 1 else 1150)
        paid = 0 if i % 4 == 1 else (due // 2 if i == 4 else due)
        owed = due - paid
        st = "√" if owed == 0 else "欠"
        if i in (2, 7):
            st = "#REF!"
        data.append([rooms[i], names[i], f"{due:,}", f"{paid:,}", f"{owed:,}", st])
    data.append(["合计", "", "", "", "?", "对不上"])
    rowh = int((h - y - 18) / len(data))
    for r, row in enumerate(data):
        cy = y + r * rowh
        fill = (247, 250, 252, 255) if r % 2 == 0 else (255, 255, 255, 255)
        if r == 0:
            fill = (235, 241, 246, 255)
        d.rectangle([0, cy, w - 1, cy + rowh], fill=fill)
        d.line([(0, cy), (w, cy)], fill=(206, 214, 222, 255), width=1)
        d.text((8, cy + 8), str(r + 1), font=font(20), fill=(140, 155, 170, 255))
        for i, cell in enumerate(row):
            cx = 46 + i * cw
            d.line([(cx, cy), (cx, cy + rowh)], fill=(206, 214, 222, 255), width=1)
            col = (30, 45, 60, 255)
            fw = "b" if r == 0 else "r"
            if cell == "#REF!":
                d.rectangle([cx + 2, cy + 2, cx + cw - 2, cy + rowh - 2], fill=(255, 226, 226, 255))
                col = (200, 40, 40, 255)
            if cell in ("欠", "?", "对不上"):
                col = (200, 40, 40, 255)
                fw = "b"
            d.text((cx + 12, cy + 7), cell, font=font(24, fw), fill=col)
    # 红色圈
    d.ellipse([46 + 2 * cw + 4, y + 7 * rowh + 2, 46 + 4 * cw - 4, y + 8 * rowh - 2],
              outline=(210, 50, 50, 200), width=3)
    # 便签
    note = Image.new("RGBA", (300, 210), (0, 0, 0, 0))
    nd = ImageDraw.Draw(note)
    nd.rounded_rectangle([0, 0, 299, 209], radius=8, fill=(255, 232, 128, 255))
    nd.text((22, 18), "月底对账", font=font(30, "b"), fill=(120, 80, 20, 255))
    nd.text((22, 62), "又差 3 户 !", font=font(30, "b"), fill=(190, 60, 40, 255))
    _scribble(nd, 22, 128, 240, rng, color=(120, 90, 40, 200))
    _scribble(nd, 22, 162, 180, rng, color=(120, 90, 40, 200))
    note = note.rotate(-7, expand=True, resample=Image.Resampling.BICUBIC)
    return im, note


def make_notebook(seed=3, w=380, h=520, label="报修记录本", color=(38, 78, 140)):
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=10, fill=color + (255,))
    d.rounded_rectangle([14, 14, w - 15, h - 15], radius=6, fill=(236, 240, 244, 255))
    # 标签贴纸
    d.rounded_rectangle([40, 46, w - 40, 128], radius=6, fill=(255, 255, 255, 255))
    d.text((w / 2, 88), label, font=font(30, "b"), fill=(40, 56, 78, 255), anchor="mm")
    # 横线
    for i in range(9):
        y = 168 + i * 38
        d.line([(30, y), (w - 30, y)], fill=(180, 194, 210, 255), width=1)
    for i in range(9):
        y = 168 + i * 38
        if rng.random() < 0.85:
            _scribble(d, 34, y - 12, rng.randint(150, w - 80), rng, gap_prob=0.16)
    # 书脊
    d.rectangle([0, 0, 10, h - 1], fill=(color[0] // 2, color[1] // 2, color[2] // 2, 255))
    return im


def make_sticky(text_lines, w=260, h=260, color=(255, 232, 128), seed=9):
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=6, fill=color + (255,))
    y = 26
    for line in text_lines:
        _scribble(d, 24, y, rng.randint(90, w - 60), rng, color=(110, 84, 36, 210))
        y += 40
    return im.rotate(rng.uniform(-8, 8), expand=True, resample=Image.Resampling.BICUBIC)


def dof(im, radius=1.2):
    return im.filter(ImageFilter.GaussianBlur(radius)) if radius > 0 else im


def make_namecard(seed=40, w=320, h=186):
    """名片：姓名手写 + 电话 + 意向车型"""
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=6, fill=(252, 252, 250, 255),
                        outline=(206, 210, 216, 255), width=1)
    d.rectangle([0, 0, 6, h - 1], fill=(46, 84, 150, 255))
    _scribble(d, 30, 46, 110, rng, color=(48, 62, 88, 225), thick=3, gap_prob=0.05)
    d.text((30, 74), "销售顾问", font=font(20), fill=(120, 134, 152, 255))
    d.text((30, 108), "138****" + str(rng.randint(1000, 9999)), font=font(24, "b"), fill=(60, 76, 100, 255))
    _scribble(d, 30, 152, 150, rng, color=(150, 160, 176, 220), thick=2)
    return im


def _wrap_chars(text, n):
    return [text[i:i + n] for i in range(0, len(text), n)]


def make_phone(seed=51, w=540, h=1010, title="张先生 · 意向 CR-V", msgs=None):
    """手机聊天界面：客户消息散落在各人手机里"""
    rng = random.Random(seed)
    if msgs is None:
        msgs = [
            ("left", "我回去和家人商量一下，\n过两天给你电话"),
            ("right", "好的张哥，那我周四上午\n再联系您，车给您留着"),
            ("left", "这周有点忙，下周再说吧"),
            ("right", "行，下周二我再跟您确认"),
            ("left", "对了，白色那个配置\n还有现车吗？"),
        ]
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=56, fill=(28, 30, 34, 255))
    d.rounded_rectangle([16, 16, w - 17, h - 17], radius=44, fill=(240, 241, 243, 255))
    # 状态栏 + 标题栏
    d.rectangle([16, 90, w - 17, 176], fill=(248, 248, 250, 255))
    d.text((w / 2, 134), title, font=font(28, "b"), fill=(40, 46, 56, 255), anchor="mm")
    d.text((40, 128), "‹", font=font(40, "b"), fill=(80, 90, 100, 255), anchor="lm")
    d.line([16, 176, w - 17, 176], fill=(220, 222, 226, 255), width=1)
    d.text((w / 2, 208), "10 月 12 日 下午 3:20", font=font(20), fill=(150, 156, 164, 255), anchor="mm")

    y = 246
    for side, txt in msgs:
        lines = []
        for seg in txt.split("\n"):
            lines += _wrap_chars(seg, 13)
        bw = min(400, max(text_w(l, 26) for l in lines) + 44)
        bh = 26 * 1.45 * len(lines) + 34
        if side == "left":
            x0 = 40
            d.rounded_rectangle([x0, y, x0 + bw, y + bh], radius=14, fill=(255, 255, 255, 255))
            col = (44, 50, 60, 255)
        else:
            x0 = w - 40 - bw
            d.rounded_rectangle([x0, y, x0 + bw, y + bh], radius=14, fill=(198, 231, 168, 255))
            col = (32, 44, 30, 255)
        for i, l in enumerate(lines):
            d.text((x0 + 22, y + 17 + i * 38), l, font=font(26), fill=col)
        y += bh + 26
    # 输入栏
    d.rectangle([16, h - 130, w - 17, h - 17], fill=(248, 248, 250, 255))
    d.rounded_rectangle([40, h - 108, w - 150, h - 42], radius=18, fill=(255, 255, 255, 255),
                        outline=(222, 224, 228, 255))
    d.text((62, h - 88), "输入消息…", font=font(24), fill=(158, 164, 172, 255))
    d.rounded_rectangle([w - 138, h - 108, w - 44, h - 42], radius=18, fill=(34, 148, 96, 255))
    d.text((w - 91, h - 75), "发送", font=font(24, "b"), fill=(255, 255, 255, 255), anchor="mm")
    return im


def make_follow_excel(seed=61, w=1180, h=860):
    """Excel 跟进表：漏记、逾期一片红"""
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=(255, 255, 255, 255))
    d.rectangle([0, 0, w - 1, 46], fill=(33, 115, 70, 255))
    d.text((16, 8), "客户跟进表 2026-10 (最终版2).xlsx", font=font(26, "b"), fill=(255, 255, 255, 255))
    cols = ["客户", "电话", "车型", "来源", "销售", "下次回访", "状态"]
    colw = [150, 190, 160, 130, 130, 210, 190]
    x = 0
    y = 46
    d.rectangle([0, y, w - 1, y + 44], fill=(235, 241, 246, 255))
    for c, cw in zip(cols, colw):
        d.text((x + 14, y + 10), c, font=font(24, "b"), fill=(54, 68, 86, 255))
        d.line([x, y, x, h], fill=(210, 216, 224, 255), width=1)
        x += cw
    rows = [
        ("王先生", "138****2210", "CR-V", "懂车帝", "小李", "10-08", "逾期 12 天"),
        ("李女士", "139****7788", "雅阁", "自然进店", "小张", "10-15", "逾期 5 天"),
        ("赵先生", "186****3344", "途观 L", "转介绍", "小王", "10-21", "待回访"),
        ("陈先生", "137****9021", "凯美瑞", "抖音", "小李", "", "跟进中"),
        ("刘女士", "188****4410", "探岳", "老客户", "小张", "", "已成交"),
        ("周先生", "135****6677", "帕萨特", "车展", "小王", "10-02", "逾期 18 天"),
        ("吴女士", "159****8823", "汉兰达", "懂车帝", "小李", "", "跟进中"),
        ("郑先生", "186****1199", "迈腾", "自然进店", "小张", "", "战败?"),
    ]
    y += 44
    rowh = 62
    for i, r in enumerate(rows):
        d.rectangle([0, y, w - 1, y + rowh], fill=(247, 250, 252, 255) if i % 2 == 0 else (255, 255, 255, 255))
        d.line([0, y, w, y], fill=(214, 220, 228, 255), width=1)
        x = 0
        for j, (val, cw) in enumerate(zip(r, colw)):
            col = (34, 46, 60, 255)
            fw = "r"
            if val.startswith("逾期"):
                col = (198, 42, 42, 255)
                fw = "b"
            if val == "":
                d.text((x + 14, y + 16), "—", font=font(24), fill=(180, 186, 194, 255))
            else:
                d.text((x + 14, y + 16), val, font=font(24, fw), fill=col)
            x += cw
        y += rowh
    # 红圈 + 批注
    for cx, cy in [(w * 0.72, 46 + 44 + 62 * 0 + 30), (w * 0.72, 46 + 44 + 62 * 5 + 30)]:
        d.ellipse([cx - 100, cy - 24, cx + 60, cy + 24], outline=(205, 50, 50, 210), width=3)
    return im


def make_quote_sheet(seed=71, w=940, h=1240, title="广告工程报价单"):
    """纸质报价单：项目 / 规格 / 数量 / 单价 / 金额"""
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=6, fill=(251, 250, 246, 255))
    d.text((w / 2, 54), title, font=font(44, "b"), fill=(44, 54, 70, 255), anchor="mm")
    d.line([60, 96, w - 60, 96], fill=(150, 160, 176, 255), width=2)
    # 客户信息行
    d.text((60, 118), "客户：", font=font(26), fill=(70, 82, 100, 255))
    _scribble(d, 130, 136, 220, rng, color=(60, 74, 96, 220))
    d.text((560, 118), "日期：2026-10-08", font=font(26), fill=(70, 82, 100, 255))
    # 表头
    top = 186
    cols = [0, 210, 430, 560, 700, w]
    heads = ["项目", "规格", "数量", "单价", "金额"]
    d.rectangle([0, top, w - 1, top + 60], fill=(228, 234, 242, 255))
    for i, hd in enumerate(heads):
        d.text((cols[i] + 16, top + 15), hd, font=font(26, "b"), fill=(60, 72, 90, 255))
    rows = [
        ("门头底板", "3mm 铝塑板", "12 ㎡", "180", "2,160"),
        ("发光字", "不锈钢 背发光", "8 个", "260", "2,080"),
        ("LED 模组", "12V 防水", "60 个", "18", "1,080"),
        ("外协喷绘", "3.2m 幅宽", "1 项", "—", "680"),
        ("安装人工", "含吊车", "1 项", "—", "1,500"),
    ]
    y = top + 60
    rowh = 88
    for i, r in enumerate(rows):
        if i % 2 == 0:
            d.rectangle([0, y, w - 1, y + rowh], fill=(246, 248, 251, 255))
        d.line([0, y, w, y], fill=(196, 206, 220, 255), width=1)
        for j, val in enumerate(r):
            d.text((cols[j] + 16, y + 28), val, font=font(26, "r" if j > 1 else "r"), fill=(40, 52, 70, 255))
        y += rowh
    for cx in cols:
        d.line([cx, top, cx, y], fill=(196, 206, 220, 255), width=1)
    # 合计
    d.rectangle([0, y, w - 1, y + 86], fill=(232, 238, 246, 255))
    d.text((430, y + 26), "报价合计", font=font(28, "b"), fill=(40, 52, 70, 255))
    d.text((w - 160, y + 22), "7,500", font=font(34, "b"), fill=(30, 44, 66, 255))
    # 手写批注
    _scribble(d, 60, y + 150, 380, rng, color=(50, 66, 92, 215), thick=3, gap_prob=0.1)
    _scribble(d, 60, y + 200, 300, rng, color=(50, 66, 92, 215), thick=3, gap_prob=0.1)
    d.ellipse([w - 300, y + 120, w - 60, y + 210], outline=(208, 48, 48, 215), width=3)
    d.text((w - 268, y + 142), "成本 ?", font=font(34, "b"), fill=(200, 46, 46, 235))
    return im


def make_material_sheet(seed=73, w=1040, h=780):
    """Excel 料价表：同一材料好几个价，谁也说不清用哪个"""
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=(255, 255, 255, 255))
    d.rectangle([0, 0, w - 1, 46], fill=(33, 115, 70, 255))
    d.text((16, 8), "材料价格表(旧)-2025.xlsx", font=font(26, "b"), fill=(255, 255, 255, 255))
    cols = ["材料", "规格", "单位", "单价", "上次进价", "备注"]
    colw = [190, 240, 110, 160, 190, 150]
    y = 46
    d.rectangle([0, y, w - 1, y + 44], fill=(235, 241, 246, 255))
    x = 0
    for c, cw in zip(cols, colw):
        d.text((x + 14, y + 10), c, font=font(24, "b"), fill=(54, 68, 86, 255))
        d.line([x, y, x, h], fill=(210, 216, 224, 255), width=1)
        x += cw
    y += 44
    rows = [
        ("铝塑板", "3mm 白/灰", "㎡", "180", "168", "涨了?"),
        ("不锈钢字", "背发光", "个", "260", "245", "外协价变"),
        ("LED 模组", "12V 防水", "个", "18", "16", ""),
        ("亚克力", "5mm 透明", "㎡", "320", "?", "没记"),
        ("喷绘布", "3.2m 幅宽", "㎡", "22", "20", ""),
        ("焊条", "304", "kg", "42", "?", ""),
        ("吊车", "8 吨", "台班", "800", "760", "临时加价"),
        ("人工", "安装 2 人", "天", "600", "600", ""),
    ]
    rowh = 62
    for i, r in enumerate(rows):
        d.rectangle([0, y, w - 1, y + rowh], fill=(247, 250, 252, 255) if i % 2 == 0 else (255, 255, 255, 255))
        d.line([0, y, w, y], fill=(214, 220, 228, 255), width=1)
        x = 0
        for j, (val, cw) in enumerate(zip(r, colw)):
            col = (34, 46, 60, 255)
            fw = "r"
            if val == "?":
                col = (198, 42, 42, 255)
                fw = "b"
            if val in ("涨了?", "没记", "外协价变"):
                col = (198, 100, 32, 255)
            d.text((x + 14, y + 16), val, font=font(24, fw), fill=col)
            x += cw
        y += rowh
    d.ellipse([190 + 42, 46 + 44 + 62 * 3 + 8, 190 + 340, 46 + 44 + 62 * 4 - 6],
              outline=(205, 50, 50, 205), width=3)
    return im


def make_folder_window(seed=91, w=1000, h=640):
    """Windows 资源管理器：一个客户一个文件夹，翻半天找不到"""
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=(255, 255, 255, 255))
    # 标题栏
    d.rectangle([0, 0, w - 1, 44], fill=(243, 243, 243, 255))
    for i, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([16 + i * 22, 16, 28 + i * 22, 28], fill=col + (255,))
    d.text((96, 10), "客户资料 - D:\\广告工程\\2026", font=font(22), fill=(70, 76, 86, 255))
    # 左侧导航
    d.rectangle([0, 44, 178, h - 26], fill=(249, 249, 251, 255))
    d.line([178, 44, 178, h - 26], fill=(228, 230, 236, 255), width=1)
    nav = ["桌面", "文档", "客户资料", "报价单", "回款明细"]
    for i, n in enumerate(nav):
        y = 62 + i * 44
        if n == "客户资料":
            d.rectangle([8, y - 6, 170, y + 30], fill=(226, 236, 252, 255))
        d.text((26, y), n, font=font(22), fill=(54, 62, 76, 255))
    # 内容区
    names = ["张记餐饮-门头", "李总-发光字", "华美地产-导视", "汽车城-围挡",
             "王工-楼顶大字", "新客户-待整理", "陈姐-喷绘", "老客户-补单"]
    x0, y0 = 206, 70
    cw, ch = 190, 118
    for i, n in enumerate(names):
        cx = x0 + (i % 4) * cw
        cy = y0 + (i // 4) * ch
        # 文件夹图标
        d.rounded_rectangle([cx + 10, cy + 14, cx + 74, cy + 30], radius=4, fill=(240, 178, 60, 255))
        d.rounded_rectangle([cx + 8, cy + 24, cx + 78, cy + 66], radius=5, fill=(255, 196, 87, 255))
        d.text((cx + 8, cy + 74), n, font=font(20), fill=(60, 68, 82, 255))
        if i < 2:
            d.text((cx + 8, cy + 96), "3 个文件 · 改了 5 版", font=font(16), fill=(150, 156, 166, 255))
    # 底部状态栏
    d.rectangle([0, h - 26, w - 1, h - 1], fill=(247, 248, 250, 255))
    d.text((12, h - 22), "8 个对象   已选 0 个", font=font(18), fill=(120, 126, 136, 255))
    return im


def make_order_excel(seed=93, w=1120, h=760):
    """Excel 台账：报价、材料、人工、杂费、利润，一堆 #REF!"""
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=(255, 255, 255, 255))
    d.rectangle([0, 0, w - 1, 46], fill=(33, 115, 70, 255))
    d.text((16, 8), "广告工程台账 2026(最终版3).xlsx", font=font(26, "b"), fill=(255, 255, 255, 255))
    cols = ["客户", "项目", "报价", "材料", "人工", "杂费", "利润"]
    colw = [170, 210, 140, 140, 130, 130, 200]
    y = 46
    d.rectangle([0, y, w - 1, y + 44], fill=(235, 241, 246, 255))
    x = 0
    for c, cw in zip(cols, colw):
        d.text((x + 12, y + 10), c, font=font(23, "b"), fill=(54, 68, 86, 255))
        d.line([x, y, x, h], fill=(210, 216, 224, 255), width=1)
        x += cw
    rows = [
        ("张记餐饮", "门头改造", "18,000", "6,200", "? ", "1,100", "#REF!"),
        ("华美地产", "导视系统", "42,000", "15,800", "3,600", "?", "#REF!"),
        ("汽车城", "围挡喷绘", "8,600", "2,900", "900", "260", "2,340"),
        ("李总", "发光字", "12,800", "4,100", "1,200", "?", "#REF!"),
        ("王工", "楼顶大字", "26,000", "9,400", "2,800", "860", "?"),
        ("陈姐", "室内喷绘", "5,200", "1,700", "600", "180", "2,720"),
        ("老客户", "补单", "3,800", "1,200", "400", "?", "#REF!"),
    ]
    y += 44
    rowh = 62
    for i, r in enumerate(rows):
        d.rectangle([0, y, w - 1, y + rowh], fill=(247, 250, 252, 255) if i % 2 == 0 else (255, 255, 255, 255))
        d.line([0, y, w, y], fill=(214, 220, 228, 255), width=1)
        x = 0
        for j, (val, cw) in enumerate(zip(r, colw)):
            col = (34, 46, 60, 255)
            fw = "r"
            if val.strip() in ("#REF!", "?", ""):
                col = (198, 42, 42, 255)
                fw = "b"
            d.text((x + 12, y + 16), val.strip() or "—", font=font(23, fw), fill=col)
            x += cw
        y += rowh
    d.ellipse([170 + 210 + 140 + 140 + 4, 46 + 44 + 62 * 4 + 6,
               170 + 210 + 140 + 140 + 136, 46 + 44 + 62 * 5 - 4],
              outline=(205, 50, 50, 200), width=3)
    return im


def make_asset_ledger(seed=111, w=900, h=1160, title="固定资产台账"):
    """手写固定资产台账：编号 / 名称 / 部门 / 使用人 / 状态"""
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=6, fill=(250, 248, 242, 255))
    d.text((w / 2, 56), title, font=font(40, "b"), fill=(48, 58, 76, 255), anchor="mm")
    d.line([40, 96, w - 40, 96], fill=(150, 162, 178, 255), width=2)
    top = 120
    cols = [0, 150, 400, 570, 700, w]
    heads = ["编号", "名称", "部门", "使用人", "状态"]
    d.rectangle([0, top, w - 1, top + 56], fill=(226, 232, 240, 255))
    for i, hd in enumerate(heads):
        d.text((cols[i] + 14, top + 14), hd, font=font(25, "b"), fill=(58, 70, 88, 255))
    rows = [
        ("A-0012", "联想 ThinkPad", "行政部", "张敏", "在用"),
        ("A-0013", "HP 打印机", "财务部", "李静", "在用"),
        ("A-0014", "投影仪", "市场部", "王强", "借出"),
        ("A-0015", "迈瑞监护仪", "设备科", "刘医生", "在用"),
        ("A-0016", "丰田 商务车", "总务", "陈师傅", "在用"),
        ("A-0017", "MacBook Pro", "设计部", "赵磊", "维修中"),
        ("A-0018", "佳能相机", "宣传科", "?", "找不到"),
        ("A-0019", "空调 3P", "会议室", "—", "在用"),
        ("A-0020", "服务器", "信息中心", "周工", "在用"),
        ("A-0021", "对讲机 x6", "保安队", "?", "账上没有"),
    ]
    y = top + 56
    rowh = 76
    for i, r in enumerate(rows):
        if i % 2 == 0:
            d.rectangle([0, y, w - 1, y + rowh], fill=(245, 247, 250, 255))
        d.line([0, y, w, y], fill=(196, 206, 220, 255), width=1)
        for j, (val, cx) in enumerate(zip(r, cols[:-1])):
            col = (44, 56, 74, 255)
            fw = "r"
            if val in ("?", "找不到", "账上没有"):
                col = (196, 46, 46, 255)
                fw = "b"
            d.text((cx + 14, y + 22), val, font=font(24, fw if j else "r"), fill=col)
        y += rowh
    for cx in cols:
        d.line([cx, top, cx, y], fill=(196, 206, 220, 255), width=1)
    # 红笔圈注 + 手写批注
    d.ellipse([cols[2] + 6, top + 56 + 76 * 6 + 6, cols[4] - 6, top + 56 + 76 * 7 - 6],
              outline=(205, 50, 50, 205), width=3)
    _scribble(d, 48, y + 56, 340, rng, color=(178, 44, 44, 215), thick=4, gap_prob=0.12)
    return im


def make_barcode_sheet(seed=113, w=880, h=560, n=6):
    """条码标签纸：一台一码"""
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=4, fill=(252, 252, 250, 255))
    lw, lh = (w - 60) // 2, (h - 60) // 3
    for i in range(n):
        x = 20 + (i % 2) * (lw + 20)
        y = 20 + (i // 2) * (lh + 10)
        d.rectangle([x, y, x + lw, y + lh], fill=(255, 255, 255, 255), outline=(206, 210, 216, 255))
        d.text((x + 14, y + 8), "资管易 · 固定资产", font=font(16), fill=(120, 128, 140, 255))
        # 条码
        bx = x + 16
        by = y + 36
        while bx < x + lw - 20:
            bw = rng.choice([2, 2, 3, 5])
            d.rectangle([bx, by, bx + bw - 1, by + 34], fill=(28, 32, 38, 255))
            bx += bw + rng.choice([2, 3, 4])
        d.text((x + 16, y + lh - 26), f"ZC-2026-{i + 12:04d}", font=font(20, "b"), fill=(40, 48, 60, 255))
    return im


def make_live_excel(seed=131, w=1140, h=800):
    """Excel 直播台账：场次 / 订单 / 佣金 全堆在一张表，扣库存靠手改"""
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=(255, 255, 255, 255))
    d.rectangle([0, 0, w - 1, 46], fill=(33, 115, 70, 255))
    d.text((16, 8), "直播台账 11月(改2).xlsx", font=font(26, "b"), fill=(255, 255, 255, 255))
    cols = ["场次", "商品", "售价", "成本", "库存", "佣金", "毛利"]
    colw = [150, 230, 130, 130, 130, 150, 220]
    y = 46
    d.rectangle([0, y, w - 1, y + 44], fill=(235, 241, 246, 255))
    x = 0
    for c, cw in zip(cols, colw):
        d.text((x + 12, y + 10), c, font=font(23, "b"), fill=(54, 68, 86, 255))
        d.line([x, y, x, h], fill=(210, 216, 224, 255), width=1)
        x += cw
    rows = [
        ("11-05 晚场", "羊毛围巾", "59", "28", "-3", "?", "#REF!"),
        ("11-05 晚场", "保温杯", "89", "42", "12", "按 15%", "?"),
        ("11-08 场", "羊绒手套", "69", "35", "手改 0", "?", "#REF!"),
        ("11-08 场", "暖手宝", "49", "22", "8", "按 15%", "12"),
        ("11-12 场", "毛毯", "129", "60", "?", "固定 20", "#REF!"),
        ("11-12 场", "睡衣", "159", "78", "5", "?", "?"),
        ("11-15 场", "拖鞋", "39", "16", "-12", "按 15%", "#REF!"),
    ]
    y += 44
    rowh = 62
    for i, r in enumerate(rows):
        d.rectangle([0, y, w - 1, y + rowh], fill=(247, 250, 252, 255) if i % 2 == 0 else (255, 255, 255, 255))
        d.line([0, y, w, y], fill=(214, 220, 228, 255), width=1)
        x = 0
        for j, (val, cw) in enumerate(zip(r, colw)):
            col = (34, 46, 60, 255)
            fw = "r"
            if val in ("#REF!", "?", "手改 0") or val.startswith("-"):
                col = (198, 42, 42, 255)
                fw = "b"
            d.text((x + 12, y + 16), val, font=font(23, fw), fill=col)
            x += cw
        y += rowh
    d.ellipse([colw[0] + colw[1] + colw[2] + colw[3] + 4, 46 + 44 + 62 * 6 + 6,
               colw[0] + colw[1] + colw[2] + colw[3] + 126, 46 + 44 + 62 * 7 - 4],
              outline=(205, 50, 50, 200), width=3)
    return im


def make_shipping_note(seed=133, w=760, h=980, title="发货单"):
    """手写发货单：单号、收件人、微信对单"""
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=6, fill=(251, 250, 246, 255))
    d.text((w / 2, 50), title, font=font(38, "b"), fill=(48, 58, 76, 255), anchor="mm")
    d.line([40, 86, w - 40, 86], fill=(150, 162, 178, 255), width=2)
    for i in range(9):
        y = 128 + i * 92
        d.text((44, y), f"{i + 1}.", font=font(24), fill=(120, 132, 150, 255))
        _scribble(d, 82, y + 22, rng.randint(150, 240), rng, gap_prob=0.15)
        _scribble(d, 350, y + 22, rng.randint(120, 250), rng, gap_prob=0.18)
        if rng.random() < 0.4:
            d.text((620, y + 4), "待确认", font=font(22, "b"), fill=(198, 46, 46, 230))
        d.line([40, y + 64, w - 40, y + 64], fill=(206, 214, 226, 255), width=1)
    return im


def make_stock_excel(seed=151, w=1120, h=780):
    """Excel 库存表：结存靠手改，改错一格整表全乱"""
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, w - 1, h - 1], fill=(255, 255, 255, 255))
    d.rectangle([0, 0, w - 1, 46], fill=(33, 115, 70, 255))
    d.text((16, 8), "库存表 11月(最终版).xlsx", font=font(26, "b"), fill=(255, 255, 255, 255))
    cols = ["商品", "编码", "单位", "入库", "出库", "结存", "预警"]
    colw = [250, 160, 100, 120, 120, 170, 200]
    y = 46
    d.rectangle([0, y, w - 1, y + 44], fill=(235, 241, 246, 255))
    x = 0
    for c, cw in zip(cols, colw):
        d.text((x + 12, y + 10), c, font=font(23, "b"), fill=(54, 68, 86, 255))
        d.line([x, y, x, h], fill=(210, 216, 224, 255), width=1)
        x += cw
    rows = [
        ("PP 打包带", "SP-0021", "卷", "120", "96", "24", "20"),
        ("纸箱 5 号", "SP-0033", "个", "800", "760", "40", "100"),
        ("封箱胶带", "SP-0044", "卷", "240", "?", "手改 60", "50"),
        ("珍珠棉", "SP-0052", "卷", "80", "62", "-8", "20"),
        ("气泡膜", "SP-0061", "卷", "60", "41", "19", "?"),
        ("五金合页", "SP-0077", "件", "400", "?", "#REF!", "150"),
        ("螺丝 M6", "SP-0088", "盒", "150", "128", "22", "30"),
        ("标签纸", "SP-0095", "卷", "90", "74", "16", "?"),
    ]
    y += 44
    rowh = 62
    for i, r in enumerate(rows):
        d.rectangle([0, y, w - 1, y + rowh], fill=(247, 250, 252, 255) if i % 2 == 0 else (255, 255, 255, 255))
        d.line([0, y, w, y], fill=(214, 220, 228, 255), width=1)
        x = 0
        for j, (val, cw) in enumerate(zip(r, colw)):
            col = (34, 46, 60, 255)
            fw = "r"
            if val in ("#REF!", "?", "手改 60") or val.startswith("-"):
                col = (198, 42, 42, 255)
                fw = "b"
            d.text((x + 12, y + 16), val, font=font(23, fw), fill=col)
            x += cw
        y += rowh
    d.ellipse([250 + 160 + 100 + 120 + 120 + 4, 46 + 44 + 62 * 2 + 6,
               250 + 160 + 100 + 120 + 120 + 156, 46 + 44 + 62 * 3 - 4],
              outline=(205, 50, 50, 200), width=3)
    return im


def make_qr(seed=171, size=420, fg=(26, 30, 38), bg=(255, 255, 255), watermark=None):
    """画一个像真的二维码：三个定位角 + 时序线 + 随机模块"""
    rng = random.Random(seed)
    n = 29
    cell = size // (n + 4)
    qsize = cell * n
    im = Image.new("RGBA", (size, size), bg + (255,))
    d = ImageDraw.Draw(im)
    ox = (size - qsize) // 2
    oy = ox

    grid = [[0] * n for _ in range(n)]

    def finder(cx, cy):
        for y in range(-1, 8):
            for x in range(-1, 8):
                gx, gy = cx + x, cy + y
                if not (0 <= gx < n and 0 <= gy < n):
                    continue
                if x in (-1, 7) or y in (-1, 7):
                    grid[gy][gx] = 0
                elif x in (0, 6) or y in (0, 6):
                    grid[gy][gx] = 1
                elif 2 <= x <= 4 and 2 <= y <= 4:
                    grid[gy][gx] = 1
                else:
                    grid[gy][gx] = 0

    finder(0, 0)
    finder(n - 7, 0)
    finder(0, n - 7)

    # 时序线
    for i in range(8, n - 8):
        grid[6][i] = 1 if i % 2 == 0 else 0
        grid[i][6] = 1 if i % 2 == 0 else 0

    # 其余随机填
    for y in range(n):
        for x in range(n):
            if (x < 9 and y < 9) or (x > n - 9 and y < 9) or (x < 9 and y > n - 9):
                continue
            if x == 6 or y == 6:
                continue
            grid[y][x] = 1 if rng.random() < 0.48 else 0

    for y in range(n):
        for x in range(n):
            if grid[y][x]:
                d.rectangle([ox + x * cell, oy + y * cell,
                             ox + (x + 1) * cell - 1, oy + (y + 1) * cell - 1], fill=fg + (255,))

    if watermark:
        lay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        txt = watermark
        fs = 30
        while text_w(txt, fs, "b") > size * 0.86 and fs > 14:
            fs -= 1
        cy = size / 2
        ld.rectangle([0, cy - fs, size, cy + fs * 1.2], fill=(255, 255, 255, 210))
        ld.text((size / 2, cy + fs * 0.1), txt, font=font(fs, "b"), fill=(120, 126, 138, 255), anchor="mm")
        im = Image.alpha_composite(im, lay)
    return im


def make_qr_site(seed=173, w=980, h=760):
    """在线二维码生成器：广告糊屏 + 水印 + 充值弹窗"""
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    d = ImageDraw.Draw(im)
    # 浏览器栏
    d.rectangle([0, 0, w - 1, 62], fill=(238, 240, 244, 255))
    for i, col in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        d.ellipse([18 + i * 22, 22, 32 + i * 22, 36], fill=col + (255,))
    d.rounded_rectangle([110, 14, w - 90, 48], radius=17, fill=(255, 255, 255, 255),
                        outline=(214, 218, 226, 255))
    d.text((126, 21), "www.mianfei-qrcode-zaixian.com", font=font(19), fill=(120, 128, 140, 255))
    d.text((w - 62, 20), "✕", font=font(24, "b"), fill=(150, 156, 166, 255))

    # 顶部广告条
    d.rectangle([0, 62, w - 1, 128], fill=(255, 232, 204, 255))
    d.text((w / 2, 84), "🎁 限时活动：开通会员 立减 30 元 · 广告位招租", font=font(22, "b"),
           fill=(186, 96, 22, 255), anchor="mm")
    d.rounded_rectangle([w - 150, 72, w - 24, 116], radius=8, fill=(240, 120, 40, 255))
    d.text((w - 87, 94), "立即开通", font=font(20, "b"), fill=(255, 255, 255, 255), anchor="mm")

    # 左侧表单
    d.text((44, 158), "内容", font=font(20), fill=(130, 136, 148, 255))
    d.rounded_rectangle([44, 188, 380, 232], radius=6, fill=(248, 249, 251, 255), outline=(222, 226, 233, 255))
    d.text((58, 198), "商品名称 / 链接…", font=font(20), fill=(160, 166, 176, 255))
    for i, lab in enumerate(["尺寸", "纠错等级", "颜色"]):
        y = 258 + i * 74
        d.text((44, y), lab, font=font(20), fill=(130, 136, 148, 255))
        for j in range(3):
            xx = 130 + j * 84
            act = (i == 0 and j == 1)
            d.rounded_rectangle([xx, y - 4, xx + 74, y + 30], radius=6,
                                fill=(66, 133, 244, 255) if act else (243, 245, 248, 255),
                                outline=None if act else (222, 226, 233, 255))
            d.text((xx + 37, y + 13), ["小", "中", "大"][j], font=font(17),
                   fill=(255, 255, 255) if act else (110, 118, 130), anchor="mm")
    d.rounded_rectangle([44, 500, 300, 556], radius=8, fill=(66, 133, 244, 255))
    d.text((172, 528), "生成二维码", font=font(22, "b"), fill=(255, 255, 255, 255), anchor="mm")
    d.text((44, 580), "⚠ 免费版导出图片带水印", font=font(18, "b"), fill=(206, 74, 40, 255))

    # 右侧二维码（带水印）
    qr = make_qr(175, 380, watermark="免费版 仅供预览")
    im.alpha_composite(qr, (450, 170))
    d.rounded_rectangle([450, 170, 830, 550], radius=10, outline=(226, 230, 236, 255), width=2)

    # 充值弹窗
    d.rounded_rectangle([470, 570, 940, 720], radius=12, fill=(255, 255, 255, 255),
                        outline=(240, 120, 40, 255), width=3)
    d.text((492, 588), "导出高清图需开通会员", font=font(24, "b"), fill=(60, 66, 78, 255))
    d.text((492, 626), "9.9 元 / 月 · 39 元 / 年", font=font(20), fill=(140, 146, 158, 255))
    d.rounded_rectangle([492, 664, 690, 706], radius=7, fill=(240, 120, 40, 255))
    d.text((591, 685), "去充值", font=font(20, "b"), fill=(255, 255, 255, 255), anchor="mm")
    d.text((710, 674), "以后再说", font=font(19), fill=(150, 156, 166, 255))
    return im


def make_price_tags(seed=177, w=820, h=980, n=6):
    """手写价签：歪歪扭扭，贴上去还行，但没法批量"""
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    names = [("纯棉毛巾", "19.9"), ("不锈钢杯", "39"), ("暖手宝", "49"),
             ("羊毛围巾", "59"), ("保温饭盒", "69"), ("棉拖鞋", "25")]
    for i in range(n):
        cw, ch = 340, 250
        x = 30 + (i % 2) * 380 + rng.randint(-10, 10)
        y = 40 + (i // 2) * 300 + rng.randint(-12, 12)
        card = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card)
        cd.rounded_rectangle([0, 0, cw - 1, ch - 1], radius=10, fill=(252, 250, 244, 255),
                             outline=(208, 202, 190, 255), width=2)
        nm, pr = names[i]
        cd.text((28, 34), nm, font=font(34, "b"), fill=(52, 60, 74, 255))
        cd.text((28, 96), "¥ " + pr, font=font(64, "b"), fill=(196, 58, 46, 255))
        _scribble(cd, 30, 190, rng.randint(120, 200), rng, color=(120, 130, 146, 220), thick=2)
        if i % 3 == 0:
            cd.text((cw - 96, 30), "手写", font=font(20), fill=(196, 120, 40, 200))
        im.alpha_composite(card.rotate(rng.uniform(-6, 6), expand=False,
                                       resample=Image.Resampling.BICUBIC), (x, y))
    return im


def make_label_sheet(seed=179, w=900, h=1100, cols=3, rows=5):
    """打印出来的标签纸：行列对不齐、有几个歪了"""
    rng = random.Random(seed)
    im = Image.new("RGBA", (w, h), (255, 255, 255, 255))
    d = ImageDraw.Draw(im)
    cw, ch = w // cols, h // rows
    for r_ in range(rows):
        for c_ in range(cols):
            x, y = c_ * cw, r_ * ch
            d.rectangle([x + 1, y + 1, x + cw - 2, y + ch - 2], outline=(224, 228, 234, 255), width=1)
            bad = rng.random() < 0.28
            dx = rng.randint(-8, 8) if bad else 0
            dy = rng.randint(-6, 6) if bad else 0
            qs = min(cw, ch) - 78
            qr = make_qr(seed + r_ * 10 + c_, qs, fg=(30, 34, 42))
            if bad:
                qr = qr.filter(ImageFilter.GaussianBlur(1.6))
            im.alpha_composite(qr, (x + (cw - qs) // 2 + dx, y + 20 + dy))
            d.text((x + cw / 2, y + ch - 34), f"SP-{r_ * cols + c_ + 21:04d}", font=font(19, "b"),
                   fill=(70, 78, 92, 255), anchor="mm")
    return im


def gradient_overlay(w, h, c1, c2, vertical=True):
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for i in range(h if vertical else w):
        t = i / (h if vertical else w)
        a = int(255 * t)
        col = (c1[0], c1[1], c1[2], int(a * c1[3])) if len(c1) > 3 else (c1[0], c1[1], c1[2], a)
        if vertical:
            d.line([(0, i), (w, i)], fill=col)
        else:
            d.line([(i, 0), (i, h)], fill=col)
    return ov
