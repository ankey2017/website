# -*- coding: utf-8 -*-
"""物管通竖屏宣传片：逐帧渲染并管道给 ffmpeg（片长/分镜由 timeline.json 决定）"""
import os, sys, json, math, random, subprocess
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
from vdraw import *  # noqa
import vdraw as V

ROOT = r"E:\vscode\zhouji\webHome"
VID = os.path.join(ROOT, "_video")
ASSET = os.path.join(ROOT, "assets", "img")

PROJ = os.environ.get("VP", "estate").strip() or "estate"
P = __import__("project_" + PROJ)

SHOT_DIR = os.path.join(ASSET, P.SLUG_DIR)
TIMELINE = os.path.join(VID, f"timeline_{PROJ}.json")
MASTER = os.path.join(VID, f"master_{PROJ}.wav")
OUTNAME = f"promo_{PROJ}.mp4"

T1 = T2 = T3 = T4 = 0.0
DUR = 45.0
TL = None
SUBS = []
BG = None
BASE = None
SHOT_IMGS = {}
BROLL = []
LOGO = None
PREVIEW = "--preview" in sys.argv

SCREENS = P.SCREENS
DEMO_SUBS = P.DEMO_SUBS
KEYWORDS = P.KEYWORDS
TAGS = P.TAGS
OFFICIAL = P.OFFICIAL
PHONE = "18929748802"


# ---------------- 初始化 ----------------
def load_timeline():
    global TL, T1, T2, T3, T4, DUR, SUBS
    with open(TIMELINE, encoding="utf-8") as f:
        TL = json.load(f)
    T1 = TL["s2"]["start"] - 0.35
    T2 = TL["s3"]["start"] - 0.35
    T3 = TL["s4"]["start"] - 0.35
    T4 = TL["total"]
    DUR = T4

    s1, s2, s3 = TL["s1"], TL["s2"], TL["s3"]
    subs = []
    for i, (f0, f1, txt) in enumerate(P.S1_SUBS):
        a = s1["start"] - 0.05 if i == 0 else s1["start"] + s1["dur"] * f0
        b = T1 if i == len(P.S1_SUBS) - 1 else s1["start"] + s1["dur"] * f1
        subs.append((a, b, txt))
    span = s2["dur"] / 9.0
    for i, txt in enumerate(DEMO_SUBS):
        subs.append((s2["start"] + i * span - 0.30 if i else T1 + 0.1,
                     s2["start"] + (i + 1) * span + 0.12, txt))
    d3 = s3["dur"]
    n3 = len(P.S3_SUBS)
    for i, (f0, f1, txt) in enumerate(P.S3_SUBS):
        a = T2 + 0.15 if i == 0 else s3["start"] + d3 * f0
        b = T3 - 0.1 if i == n3 - 1 else s3["start"] + d3 * f1
        subs.append((a, b, txt))
    SUBS = subs


def build_desk(w=1400, h=2400):
    im = Image.new("RGBA", (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        d.line([(0, y), (w, y)], fill=lerp_color((46, 40, 34), (22, 20, 18), y / h))
    rng = random.Random(5)
    for _ in range(300):
        x, y = rng.randint(0, w), rng.randint(0, h)
        ln = rng.randint(60, 320)
        d.line([(x, y), (x + ln, y + rng.randint(-3, 3))], fill=(255, 240, 220, rng.randint(4, 12)))
    return im


def build_broll():
    if P.BROLL == "estate":
        return build_broll_estate()
    if P.BROLL == "crm":
        return build_broll_crm()
    if P.BROLL == "asset":
        return build_broll_asset()
    if P.BROLL == "live":
        return build_broll_live()
    return build_broll_ad()


def build_broll_estate():
    W2, H2 = 1400, 2400
    shots = []

    a = build_desk(W2, H2)
    led1 = make_ledger(1, 860, 1180).rotate(6, expand=True, resample=Image.Resampling.BICUBIC)
    led2 = make_ledger(4, 860, 1180).rotate(-9, expand=True, resample=Image.Resampling.BICUBIC)
    a.alpha_composite(dof(led1, 0.4), (150, 600))
    a.alpha_composite(dof(led2, 0.6), (500, 880))
    ex = make_excel(2, 980, 700)
    a.alpha_composite(dof(ex[0], 0.5), (210, 1480))
    a.alpha_composite(ex[1], (880, 1700))
    nb = make_notebook(3, 400, 540, "报修记录本", (150, 60, 50)).rotate(-14, expand=True, resample=Image.Resampling.BICUBIC)
    a.alpha_composite(dof(nb, 0.5), (30, 260))
    a.alpha_composite(make_sticky(["月底对账", "差 3 户"], 260, 240, seed=11), (960, 720))
    shots.append(a)

    b = build_desk(W2, H2)
    ex2 = make_excel(6, 1150, 820)[0].rotate(-3, expand=True, resample=Image.Resampling.BICUBIC)
    b.alpha_composite(dof(ex2, 0.2), (100, 660))
    led3 = make_ledger(8, 900, 1250).rotate(13, expand=True, resample=Image.Resampling.BICUBIC)
    b.alpha_composite(dof(led3, 1.4), (660, 120))
    b.alpha_composite(make_sticky(["改一处", "漏三处"], 300, 260, seed=13), (820, 1560))
    shots.append(b)

    c = build_desk(W2, H2)
    specs = [("报修登记本", (152, 62, 52), -9, 200), ("停车记录本", (36, 82, 132), 5, 470),
             ("访客登记本", (58, 110, 92), -4, 700)]
    for i, (lb, col, ang, y) in enumerate(specs):
        nb = make_notebook(20 + i, 420, 580, lb, col).rotate(ang, expand=True, resample=Image.Resampling.BICUBIC)
        c.alpha_composite(dof(nb, 0.35), (150 + i * 300, y))
    ex3 = make_excel(9, 1020, 720)[0].rotate(4, expand=True, resample=Image.Resampling.BICUBIC)
    c.alpha_composite(dof(ex3, 0.8), (300, 1400))
    c.alpha_composite(make_sticky(["四个口径", "对不上"], 300, 260, seed=17), (800, 500))
    shots.append(c)
    return shots


def build_broll_crm():
    """汽车门店三组画面：客户登记本 / 客户在销售手机里 / Excel 跟进表"""
    W2, H2 = 1400, 2400
    shots = []

    # A：前台登记本 + 名片
    a = build_desk(W2, H2)
    nb1 = make_notebook(31, 460, 620, "客户登记本", (120, 52, 48)).rotate(-11, expand=True, resample=Image.Resampling.BICUBIC)
    a.alpha_composite(dof(nb1, 0.5), (90, 520))
    for i, off in enumerate([(0, 0), (26, 18), (52, 36)]):
        a.alpha_composite(dof(make_namecard(seed=40 + i), 0.4), (620 + off[0], 1500 + off[1]))
    a.alpha_composite(make_sticky(["电话没存？", "又跑了 3 个"], 300, 260, seed=23), (900, 520))
    exA = make_excel(33, 1000, 720)[0].rotate(7, expand=True, resample=Image.Resampling.BICUBIC)
    a.alpha_composite(dof(exA, 0.9), (560, 980))
    shots.append(a)

    # B：客户都在销售手机里
    b = build_desk(W2, H2)
    ph = make_phone(seed=51).rotate(-4, expand=True, resample=Image.Resampling.BICUBIC)
    b.alpha_composite(dof(ph, 0.25), (330, 460))
    nb2 = make_notebook(37, 420, 560, "意向客户", (60, 78, 120)).rotate(12, expand=True, resample=Image.Resampling.BICUBIC)
    b.alpha_composite(dof(nb2, 1.2), (30, 1450))
    b.alpha_composite(make_sticky(["聊完就忘", "下次没约"], 290, 250, seed=29), (900, 1560))
    shots.append(b)

    # C：Excel 跟进表，红圈一片
    c = build_desk(W2, H2)
    exC = make_follow_excel(seed=61, w=1180, h=860).rotate(-3, expand=True, resample=Image.Resampling.BICUBIC)
    c.alpha_composite(dof(exC, 0.2), (90, 620))
    nb3 = make_notebook(41, 400, 540, "回访提醒", (46, 100, 92)).rotate(-13, expand=True, resample=Image.Resampling.BICUBIC)
    c.alpha_composite(dof(nb3, 1.4), (860, 140))
    c.alpha_composite(make_sticky(["谁跟到哪了？"], 300, 240, seed=31), (200, 1560))
    shots.append(c)
    return shots


def build_broll_ad():
    """广告工程三组画面：报价单与料单 / 欠款记在微信里 / 料价表对不上"""
    W2, H2 = 1400, 2400
    shots = []

    # A：报价单 + 料单 + 计算器
    a = build_desk(W2, H2)
    q1 = make_quote_sheet(71, 940, 1240).rotate(-5, expand=True, resample=Image.Resampling.BICUBIC)
    a.alpha_composite(dof(q1, 0.35), (110, 420))
    q2 = make_quote_sheet(76, 900, 1180, "门头工程报价单").rotate(9, expand=True, resample=Image.Resampling.BICUBIC)
    a.alpha_composite(dof(q2, 0.9), (520, 1320))
    a.alpha_composite(make_sticky(["这单到底", "赚多少？"], 300, 260, seed=77), (830, 520))
    nb = make_notebook(79, 380, 500, "外协付款", (120, 70, 40)).rotate(-13, expand=True, resample=Image.Resampling.BICUBIC)
    a.alpha_composite(dof(nb, 0.7), (20, 1700))
    shots.append(a)

    # B：欠款记在微信里
    b = build_desk(W2, H2)
    ph = make_phone(81, title="王总 · 门头工程", msgs=[
        ("left", "这批门头先做，尾款\n下个月初给你"),
        ("right", "好的王总，那我先备料"),
        ("left", "对了上次那个字\n是不是算贵了？"),
        ("right", "我查一下……料价还得问一下"),
        ("left", "你查清楚发我，我这边\n也要对账"),
    ]).rotate(4, expand=True, resample=Image.Resampling.BICUBIC)
    b.alpha_composite(dof(ph, 0.25), (380, 420))
    nb2 = make_notebook(83, 400, 520, "欠款记录", (46, 80, 120)).rotate(-11, expand=True, resample=Image.Resampling.BICUBIC)
    b.alpha_composite(dof(nb2, 1.2), (30, 1560))
    b.alpha_composite(make_sticky(["欠多少", "谁记得住"], 290, 250, seed=85), (930, 1500))
    shots.append(b)

    # C：料价表，一堆问号
    c = build_desk(W2, H2)
    mt = make_material_sheet(73, 1080, 810).rotate(-3, expand=True, resample=Image.Resampling.BICUBIC)
    c.alpha_composite(dof(mt, 0.2), (150, 700))
    q3 = make_quote_sheet(87, 820, 1080, "用料清单").rotate(13, expand=True, resample=Image.Resampling.BICUBIC)
    c.alpha_composite(dof(q3, 1.5), (740, 120))
    c.alpha_composite(make_sticky(["料价三个版本", "用哪个？"], 320, 250, seed=89), (170, 1640))
    shots.append(c)
    return shots


def build_broll_asset():
    """固定资产三组画面：手写台账 / Excel 多版本 / 找不到的设备和条码"""
    W2, H2 = 1400, 2400
    shots = []

    # A：手写台账 + 领用条子
    a = build_desk(W2, H2)
    led = make_asset_ledger(111, 920, 1180).rotate(-6, expand=True, resample=Image.Resampling.BICUBIC)
    a.alpha_composite(dof(led, 0.35), (130, 500))
    nb = make_notebook(115, 400, 520, "领用登记", (52, 84, 128)).rotate(11, expand=True, resample=Image.Resampling.BICUBIC)
    a.alpha_composite(dof(nb, 0.9), (620, 1420))
    a.alpha_composite(make_sticky(["这条子是谁写的？"], 320, 230, seed=117), (860, 470))
    shots.append(a)

    # B：Excel 好多个版本
    b = build_desk(W2, H2)
    ex = make_order_excel(119, 1120, 760).rotate(4, expand=True, resample=Image.Resampling.BICUBIC)
    b.alpha_composite(dof(ex, 0.25), (120, 620))
    nb2 = make_notebook(121, 400, 520, "盘点草稿", (120, 78, 46)).rotate(-12, expand=True, resample=Image.Resampling.BICUBIC)
    b.alpha_composite(dof(nb2, 1.3), (760, 1500))
    b.alpha_composite(make_sticky(["台账 3 个版本", "哪个是准的？"], 320, 250, seed=123), (700, 320))
    shots.append(b)

    # C：条码标签 + 对不上的设备
    c = build_desk(W2, H2)
    bc = make_barcode_sheet(113, 960, 610).rotate(-8, expand=True, resample=Image.Resampling.BICUBIC)
    c.alpha_composite(dof(bc, 0.3), (110, 520))
    led2 = make_asset_ledger(127, 900, 1160).rotate(9, expand=True, resample=Image.Resampling.BICUBIC)
    c.alpha_composite(dof(led2, 1.1), (430, 1180))
    c.alpha_composite(make_sticky(["这台在谁手上"], 300, 240, seed=129), (830, 1290))
    shots.append(c)
    return shots


def build_broll_live():
    """直播带货三组画面：手写发货单 / Excel 台账 / 微信对单与样品条子"""
    W2, H2 = 1400, 2400
    shots = []

    # A：手写发货单 + 手机后台
    a = build_desk(W2, H2)
    sn = make_shipping_note(133, 780, 1000).rotate(-7, expand=True, resample=Image.Resampling.BICUBIC)
    a.alpha_composite(dof(sn, 0.35), (120, 480))
    ph = make_phone(135, title="小张 · 要货", msgs=[
        ("left", "那件毛毯还有吗？\n直播间说有的"),
        ("right", "我看一下库存哈"),
        ("left", "顺便问下佣金\n怎么算的？"),
        ("right", "我翻下本子……"),
        ("left", "算好了发我"),
    ]).rotate(5, expand=True, resample=Image.Resampling.BICUBIC)
    a.alpha_composite(dof(ph, 0.8), (640, 1420))
    a.alpha_composite(make_sticky(["到底还剩几件？"], 320, 230, seed=137), (860, 500))
    shots.append(a)

    # B：Excel 台账，一堆 #REF!
    b = build_desk(W2, H2)
    ex = make_live_excel(131, 1160, 820).rotate(-3, expand=True, resample=Image.Resampling.BICUBIC)
    b.alpha_composite(dof(ex, 0.2), (90, 640))
    nb = make_notebook(139, 400, 540, "样品领用", (58, 92, 132)).rotate(12, expand=True, resample=Image.Resampling.BICUBIC)
    b.alpha_composite(dof(nb, 1.3), (740, 1460))
    b.alpha_composite(make_sticky(["库存手改", "改错了"], 300, 250, seed=141), (700, 320))
    shots.append(b)

    # C：一桌子的样品 + 条子 + 计算器
    c = build_desk(W2, H2)
    nb2 = make_notebook(143, 440, 580, "样品借出", (120, 70, 46)).rotate(-11, expand=True, resample=Image.Resampling.BICUBIC)
    c.alpha_composite(dof(nb2, 0.4), (100, 520))
    sn2 = make_shipping_note(145, 720, 940, "退换货记录").rotate(8, expand=True, resample=Image.Resampling.BICUBIC)
    c.alpha_composite(dof(sn2, 0.9), (560, 900))
    c.alpha_composite(make_sticky(["佣金拿计算器", "算三遍"], 320, 250, seed=147), (820, 460))
    ex2 = make_live_excel(149, 1100, 780).rotate(5, expand=True, resample=Image.Resampling.BICUBIC)
    c.alpha_composite(dof(ex2, 1.5), (280, 1520))
    shots.append(c)
    return shots


def init_assets():
    global BG, BASE, BROLL, S3BG
    load_timeline()
    BG = make_background()
    BASE = BG.convert("RGBA")
    BASE.alpha_composite(make_scrim(1380, 1920, 0.74))
    for title, fn, note, tgt in SCREENS:
        SHOT_IMGS[fn] = Image.open(os.path.join(SHOT_DIR, fn)).convert("RGB")
    BROLL = build_broll()

    # 场景三背景：软件界面虚化铺底，避免整段过暗
    src = SHOT_IMGS[SCREENS[0][1]]
    scale = max(W / src.width, H / src.height) * 1.15
    tw, th = int(src.width * scale), int(src.height * scale)
    tex = src.resize((tw, th), Image.Resampling.LANCZOS)
    left = (tw - W) // 2
    top = (th - H) // 2 - 40
    tex = tex.crop((left, top, left + W, top + H)).filter(ImageFilter.GaussianBlur(16)).convert("RGBA")
    tex.alpha_composite(Image.new("RGBA", (W, H), (10, 27, 50, 208)))
    S3BG = tex


def s3_backdrop(p):
    if S3BG is None:
        return None
    if p >= 0.995:
        return S3BG
    im = S3BG.copy()
    a = im.split()[3].point(lambda v: int(v * clamp(p)))
    im.putalpha(a)
    return im


# ---------------- 顶部 / 字幕 ----------------
def draw_topbar(img, t, label, idx=None, total=None):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 5], fill=(255, 255, 255, 30))
    d.rectangle([0, 0, W * clamp(t / max(0.1, DUR)), 5], fill=BLUE + (240,))
    brand = f"{P.NAME} {P.NAME_EN}"
    lw = text_w(brand, 27, "b") + 54
    pill(img, 56, 86, lw, 54, brand, 27, WHITE, (255, 255, 255, 22))
    if idx is not None:
        draw_text(img, (W - 56, 113), f"{idx:02d} / {total:02d}", 28, MUTED, "b", anchor="rm")
    else:
        draw_text(img, (W - 56, 113), label, 28, MUTED, "b", anchor="rm")


def draw_subtitles(img, t):
    for s, e, txt in SUBS:
        if s <= t < e:
            p = clamp((t - s) / 0.24)
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            draw_rich(layer, txt, 1650 + int(16 * (1 - ease_out(p))), 45, max_w=950,
                      color=WHITE, hl_color=BLUE_L, weight="b", line_gap=1.32,
                      shadow=(0, 3, (2, 8, 18, 200)))
            if p < 1:
                a = layer.split()[3].point(lambda v: int(v * ease_out(p)))
                layer.putalpha(a)
            img.alpha_composite(layer)
            break


# ---------------- 场景 1 ----------------
def scene_broll(img, t):
    shots = [(0.0, 2.9, 0), (2.9, 6.1, 1), (6.1, T1 + 0.4, 2)]
    cur = shots[-1]
    for s, e, i in shots:
        if s <= t < e:
            cur = (s, e, i)
    s, e, i = cur
    p = clamp((t - s) / max(0.1, e - s))

    def render(idx, lp):
        src = BROLL[idx]
        z = lerp(1.0, 1.09, ease_in_out(lp))
        cw, ch = W / z, H / z
        cx = src.width / 2 + (idx - 1) * 26 * lp
        cy = src.height / 2 - 30 + (24 if idx % 2 else -24) * lp
        crop = src.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2)))
        return crop.resize((W, H), Image.Resampling.LANCZOS)

    frame = render(i, p)
    if s > 0 and t - s < 0.24:
        prev = [x for x in shots if abs(x[1] - s) < 1e-6][0][2]
        a = ease_in_out((t - s) / 0.24)
        frame = Image.blend(render(prev, 1.0), frame, a)

    frame = frame.convert("RGBA")
    frame.alpha_composite(Image.new("RGBA", (W, H), (4, 10, 20, getattr(P, "OVERLAY", 128))))
    frame.alpha_composite(make_scrim(0, 560, 0.55))
    img.alpha_composite(frame)

    tags = TAGS
    p2 = clamp((t - s) / 0.32)
    if p2 > 0:
        tag = tags[i]
        lw = text_w(tag, 30, "b") + 56
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        pill(layer, 56, 300 + int(14 * (1 - ease_out(p2))), lw, 58, tag, 30, WHITE, (26, 64, 132, 205))
        a = layer.split()[3].point(lambda v: int(v * ease_out(p2)))
        layer.putalpha(a)
        img.alpha_composite(layer)

    draw_subtitles(img, t)


# ---------------- 场景 2 ----------------
CARD_X, CARD_Y, CARD_W, CARD_H = 40, 430, 1000, 592


def draw_keywords(img, k, y):
    words = KEYWORDS[k]
    size, h, pad, gap = 30, 62, 46, 14
    widths = [text_w(w, size, "b") + pad for w in words]
    total = sum(widths) + gap * (len(words) - 1)
    x = (W - total) / 2
    for i, w in enumerate(words):
        pill(img, x, y, widths[i], h, w, size, BLUE_L, (46, 123, 255, 26), border=(46, 123, 255, 110))
        x += widths[i] + gap


def screen_frame(fn, zoom, drift):
    src = SHOT_IMGS[fn]
    s = CARD_W / src.width * zoom
    cw, ch = CARD_W / s, CARD_H / s
    cx = src.width / 2 + drift * max(0.0, (src.width - cw) / 2)
    cy = src.height / 2 + drift * 0.3 * max(0.0, (src.height - ch) / 2)
    return src.crop((int(cx - cw / 2), int(cy - ch / 2), int(cx + cw / 2), int(cy + ch / 2))).resize(
        (CARD_W, CARD_H), Image.Resampling.LANCZOS)


def scene_demo(img, t):
    span = TL["s2"]["dur"] / 9.0
    k = int((t - TL["s2"]["start"] + 0.30) / span)
    k = max(0, min(8, k))
    local = t - (TL["s2"]["start"] - 0.30 + k * span)
    p = clamp(local / span)
    title, fn, note, tgt = SCREENS[k]

    draw_text(img, (56, 208), f"{k + 1:02d}", 30, BLUE_L, "b")
    draw_text(img, (112, 202), title.split(" ", 1)[1], 52, WHITE, "b")

    cur = screen_frame(fn, lerp(1.0, 1.045, ease_in_out(p)), lerp(-1, 1, p))
    dy = 0
    if k > 0 and local < 0.26:
        a = ease_in_out(local / 0.26)
        prev = screen_frame(SCREENS[k - 1][1], 1.045, 1.0)
        cur = Image.blend(prev, cur, a)
        dy = int(-24 * (1 - a))

    x, y = CARD_X, CARD_Y + dy
    paste_card(img, x, y, CARD_W, CARD_H, 20, (255, 255, 255, 255), (30, 16, 0.60))
    paste_rounded(img, cur, x, y, CARD_W, CARD_H, 20, border=(255, 255, 255, 38))

    draw_text(img, (56, CARD_Y + CARD_H + 44), note, 31, MUTED, "r")
    draw_keywords(img, k, CARD_Y + CARD_H + 112)

    rail_x = 1046
    y0 = CARD_Y + CARD_H / 2 - 4 * 26
    for i in range(9):
        yy = y0 + i * 26
        if i == k:
            ImageDraw.Draw(img).rounded_rectangle([rail_x - 4, yy - 9, rail_x + 4, yy + 9], radius=4, fill=BLUE + (255,))
        else:
            ImageDraw.Draw(img).ellipse([rail_x - 4, yy - 4, rail_x + 4, yy + 4], fill=(255, 255, 255, 60))

    px = x + CARD_W * (0.32 + tgt[0] * 0.40)
    py = y + CARD_H * (0.50 + tgt[1] * 0.28)
    sx, sy = x + CARD_W * 0.66, y + CARD_H * 0.90
    mv = ease_in_out(clamp(local / 0.85))
    cx = lerp(sx, px, mv)
    cy = lerp(sy, py, mv) - 30 * math.sin(math.pi * mv)
    scale = 1.0
    if local > 0.85:
        cp = local - 0.85
        draw_ripple(img, px, py, cp / 0.65)
        if cp < 0.12:
            scale = lerp(1.0, 0.86, cp / 0.12)
    draw_cursor(img, cx, cy, 255, scale)

    draw_subtitles(img, t)


# ---------------- 场景 3 ----------------
CHIPS = P.CHIPS
ROWS = P.ROWS


def scene_suit(img, t):
    lt = t - T2
    span = max(4.0, T3 - T2)
    bg = s3_backdrop(clamp(lt / 0.45))
    if bg is not None:
        img.alpha_composite(bg)
    draw_text(img, (56, 208), "适配场景", 30, BLUE_L, "b")
    draw_text(img, (56, 250), "谁在用", 52, WHITE, "b")

    fade_chips = clamp((span * 0.50 - lt) / 0.5, 0, 1)
    for i, c in enumerate(CHIPS):
        p = clamp((lt - (0.45 + i * 0.62)) / 0.42)
        if p <= 0:
            continue
        bw, bh = 470, 96
        bx = 56 + (i % 2) * (bw + 22)
        by = 356 + (i // 2) * (bh + 18) + int(18 * (1 - ease_out(p)))
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=16,
                            fill=(255, 255, 255, 30), outline=(120, 170, 240, 120))
        d.ellipse([bx + 26, by + 34, bx + 54, by + 62], fill=BLUE + (235,))
        d.text((bx + 76, by + bh / 2), c, font=font(36, "b"), fill=WHITE, anchor="lm")
        a = layer.split()[3].point(lambda v: int(v * ease_out(p) * fade_chips))
        layer.putalpha(a)
        img.alpha_composite(layer)

    cp = clamp((lt - span * 0.40) / 0.55)
    if cp > 0:
        cy = 830 + int(90 * (1 - ease_out(cp)))
        op = ease_out(cp)
        layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        paste_shadow(layer, 50, cy, 980, 470, 22, blur=26, alpha=int(150 * op), dy=12)
        d = ImageDraw.Draw(layer)
        d.rounded_rectangle([50, cy, 1030, cy + 470], radius=22,
                            fill=(19, 38, 66, int(242 * op)), outline=(96, 148, 214, int(120 * op)), width=2)
        for i in range(3):
            ly = cy + 140 + i * 108
            d.line([(84, ly), (996, ly)], fill=(120, 160, 210, int(46 * op)))
        d.text((100, cy + 8), "对比项", font=font(22, "r"), fill=(126, 152, 184, int(255 * op)))
        d.text((1000, cy + 8), "实际用起来", font=font(22, "r"), fill=(126, 152, 184, int(255 * op)), anchor="ra")
        for i, (name, desc, hi) in enumerate(ROWS):
            ap = clamp((lt - (span * 0.44 + i * 0.72)) / 0.45)
            if ap <= 0:
                continue
            ry = cy + 44 + i * 108
            if hi:
                d.rounded_rectangle([64, ry - 6, 1016, ry + 84], radius=14,
                                    fill=(34, 96, 190, int(70 * ap)), outline=BLUE_L + (int(170 * ap),), width=2)
                d.rounded_rectangle([64, ry - 6, 70, ry + 84], radius=3, fill=BLUE_L + (int(255 * ap),))
            d.text((104, ry + 22), name, font=font(37, "b" if hi else "r"),
                   fill=(BLUE_L if hi else (232, 239, 248)) + (int(255 * ap),))
            d.text((996, ry + 27), desc, font=font(29, "b" if hi else "r"),
                   fill=(BLUE_L if hi else (176, 194, 216)) + (int(255 * ap),), anchor="ra")
        img.alpha_composite(layer)

    draw_subtitles(img, t)


# ---------------- 场景 4 ----------------
def scene_poster_xhs(img, t):
    """小红书专版收尾：不留官网与电话，改为评论区互动引导"""
    global LOGO
    if LOGO is None:
        LOGO = Image.open(os.path.join(ASSET, "linzi-logo-white.png")).convert("RGBA")
    p = clamp((t - T3) / 0.7)
    op = ease_out(p)
    a = int(255 * op)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.alpha_composite(Image.new("RGBA", (W, H), (9, 26, 50, int(246 * op))))

    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([-220, 20, W + 220, 900], fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(170)).point(lambda v: int(v * 0.50 * op))
    layer.alpha_composite(Image.composite(Image.new("RGBA", (W, H), (58, 124, 218, 255)),
                                          Image.new("RGBA", (W, H), (0, 0, 0, 0)), glow))

    lw = 400
    lh = int(LOGO.height * lw / LOGO.width)
    layer.alpha_composite(LOGO.resize((lw, lh), Image.Resampling.LANCZOS), (int(W / 2 - lw / 2), 210))

    d = ImageDraw.Draw(layer)
    d.text((W / 2, 528), f"{P.NAME} {P.NAME_EN}", font=font(62, "b"), fill=WHITE + (a,), anchor="mm")
    d.rounded_rectangle([W / 2 - 120, 600, W / 2 + 120, 604], radius=2, fill=BLUE + (int(220 * op),))

    # 主标语
    sl = 46
    while text_w(P.SLOGAN, sl, "b") > 940 and sl > 26:
        sl -= 1
    d.text((W / 2, 690), P.SLOGAN, font=font(sl, "b"), fill=WHITE + (a,), anchor="mm")

    # 互动提问卡
    p2 = clamp((t - T3 - 0.9) / 0.7)
    if p2 > 0:
        a2 = int(255 * ease_out(p2))
        cw, chh = 890, 300
        cx, cy = (W - cw) / 2, 830
        d.rounded_rectangle([cx, cy, cx + cw, cy + chh], radius=24,
                            fill=(255, 255, 255, int(20 * ease_out(p2))),
                            outline=(120, 170, 240, int(120 * ease_out(p2))), width=2)
        d.text((W / 2, cy + 62), "你们单位的资产台账", font=font(38, "r"),
               fill=(206, 220, 240) + (a2,), anchor="mm")
        d.text((W / 2, cy + 126), "现在是怎么管的？", font=font(48, "b"),
               fill=WHITE + (a2,), anchor="mm")
        d.text((W / 2, cy + 210), "评论区聊聊，我看到都会回", font=font(30, "r"),
               fill=BLUE_L + (a2,), anchor="mm")
        # 抖动的小手指向下
        dy = int(6 * math.sin((t - T3) * 4.2))
        d.text((W / 2, cy + 258 + dy), "👇", font=font(40), fill=(255, 214, 102) + (a2,), anchor="mm")

    # 卖点三条
    p3 = clamp((t - T3 - 1.8) / 0.6)
    if p3 > 0:
        a3 = int(255 * ease_out(p3))
        chips = ["一套台账", "断网也能用", "一次付费"]
        cw2, gap = 268, 14
        start = (W - (len(chips) * cw2 + (len(chips) - 1) * gap)) / 2
        for i, c in enumerate(chips):
            x = start + i * (cw2 + gap)
            d.rounded_rectangle([x, 1210, x + cw2, 1266], radius=28,
                                fill=(255, 255, 255, int(18 * ease_out(p3))),
                                outline=(130, 175, 240, int(70 * ease_out(p3))))
            d.text((x + cw2 / 2, 1238), c, font=font(26, "r"), fill=(216, 228, 244) + (a3,), anchor="mm")

    # 关注引导
    p4 = clamp((t - T3 - 2.6) / 0.6)
    if p4 > 0:
        a4 = int(255 * ease_out(p4))
        d.text((W / 2, 1380), "关注我 · 看更多管理实操", font=font(32, "b"),
               fill=(255, 255, 255, a4), anchor="mm")

    d.text((W / 2, 1742), P.SUB_SLOGAN, font=font(26, "r"), fill=DIM + (a,), anchor="mm")
    img.alpha_composite(layer)


def scene_poster(img, t):
    if getattr(P, "POSTER_MODE", "") == "xhs":
        return scene_poster_xhs(img, t)
    global LOGO
    if LOGO is None:
        LOGO = Image.open(os.path.join(ASSET, "linzi-logo-white.png")).convert("RGBA")
    p = clamp((t - T3) / 0.7)
    op = ease_out(p)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    layer.alpha_composite(Image.new("RGBA", (W, H), (9, 26, 50, int(244 * op))))

    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse([-220, 40, W + 220, 880], fill=255)
    glow = glow.filter(ImageFilter.GaussianBlur(170)).point(lambda v: int(v * 0.46 * op))
    layer.alpha_composite(Image.composite(Image.new("RGBA", (W, H), (60, 126, 220, 255)),
                                          Image.new("RGBA", (W, H), (0, 0, 0, 0)), glow))

    lw = 440
    lh = int(LOGO.height * lw / LOGO.width)
    layer.alpha_composite(LOGO.resize((lw, lh), Image.Resampling.LANCZOS), (int(W / 2 - lw / 2), 268))

    d = ImageDraw.Draw(layer)
    a = int(255 * op)
    d.text((W / 2, 604), f"{P.NAME} {P.NAME_EN}", font=font(66, "b"), fill=WHITE + (a,), anchor="mm")
    d.rounded_rectangle([W / 2 - 130, 682, W / 2 + 130, 686], radius=2, fill=BLUE + (int(220 * op),))

    d.text((W / 2, 762), "官 网", font=font(30, "r"), fill=MUTED + (a,), anchor="ma")
    us = 36
    while text_w(OFFICIAL, us, "b") > 958 and us > 20:
        us -= 1
    d.text((W / 2, 822), OFFICIAL, font=font(us, "b"), fill=WHITE + (a,), anchor="ma")

    d.text((W / 2, 968), "联系电话", font=font(30, "r"), fill=MUTED + (a,), anchor="ma")
    d.text((W / 2, 1064), PHONE, font=font(100, "b"), fill=WHITE + (a,), anchor="mm")
    d.text((W / 2, 1140), "（微信同号）", font=font(34, "r"), fill=BLUE_L + (a,), anchor="ma")

    chips = ["一次付费永久使用", "本地保存数据", "断网离线可用"]
    cw, gap = 300, 16
    start = (W - (len(chips) * cw + (len(chips) - 1) * gap)) / 2
    for i, c in enumerate(chips):
        x = start + i * (cw + gap)
        d.rounded_rectangle([x, 1268, x + cw, 1326], radius=29,
                            fill=(255, 255, 255, int(16 * op)), outline=(130, 175, 240, int(66 * op)))
        d.text((x + cw / 2, 1297), c, font=font(26, "r"), fill=(216, 228, 244) + (a,), anchor="mm")

    sl = 40
    while text_w(P.SLOGAN, sl, "b") > 1000 and sl > 24:
        sl -= 1
    d.text((W / 2, 1700), P.SLOGAN, font=font(sl, "b"), fill=WHITE + (a,), anchor="mm")
    d.text((W / 2, 1772), P.SUB_SLOGAN, font=font(26, "r"),
           fill=DIM + (a,), anchor="mm")
    img.alpha_composite(layer)


# ---------------- 主循环 ----------------
def render_frame(t):
    img = BASE.copy()
    if t < T1:
        scene_broll(img, t)
        draw_topbar(img, t, "痛点")
    elif t < T2:
        scene_demo(img, t)
        idx = int((t - TL["s2"]["start"] + 0.30) / (TL["s2"]["dur"] / 9.0)) + 1
        draw_topbar(img, t, "功能", max(1, min(9, idx)), 9)
    elif t < T3:
        scene_suit(img, t)
        draw_topbar(img, t, "适配")
    else:
        scene_poster(img, t)
        ImageDraw.Draw(img).rectangle([0, 0, W * clamp(t / DUR), 5], fill=BLUE + (240,))
    return img.convert("RGB")


def main():
    init_assets()
    if PREVIEW:
        for s in sys.argv:
            if s.startswith("--t="):
                tt = float(s.split("=")[1])
                render_frame(tt).save(os.path.join(VID, f"preview_{PROJ}_{tt:05.1f}.png"))
        print("preview ok")
        return

    out = os.path.join(VID, OUTNAME)
    audio = MASTER
    ff = __import__("imageio_ffmpeg").get_ffmpeg_exe()
    cmd = [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if os.path.exists(audio):
        cmd += ["-i", audio]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
            "-profile:v", "high", "-movflags", "+faststart"]
    if os.path.exists(audio):
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += [out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    total = int(round(DUR * FPS))
    for i in range(total):
        proc.stdin.write(render_frame(i / FPS).tobytes())
        if i % 200 == 0:
            print(f"frame {i}/{total}", flush=True)
    proc.stdin.close()
    err = proc.stderr.read().decode("utf-8", "ignore")
    proc.wait()
    with open(os.path.join(VID, "ffmpeg_log.txt"), "w", encoding="utf-8") as f:
        f.write(err[-3000:])
    print("done", out, DUR)


if __name__ == "__main__":
    main()
