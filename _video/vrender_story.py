# -*- coding: utf-8 -*-
"""广告工程经营管理经验分享（小红书风格，米白笔记体，第一人称口播）"""
import os, sys, json, math, re, random, subprocess
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(__file__))
from vdraw import *  # noqa

ROOT = r"E:\vscode\zhouji\webHome"
VID = os.path.join(ROOT, "_video")
ASSET = os.path.join(ROOT, "assets", "img")
P = __import__("project_adstory")

SHOT_DIR = os.path.join(ASSET, P.SLUG_DIR)
TIMELINE = os.path.join(VID, "timeline_adstory.json")
MASTER = os.path.join(VID, "master_adstory.wav")
OUT = os.path.join(VID, "promo_adstory.mp4")

CREAM1, CREAM2 = (249, 244, 233), (230, 216, 196)
INK, INK2, MUTED = (33, 39, 49), (74, 82, 94), (142, 148, 158)
HL = (28, 86, 214)
ACC = (219, 84, 52)
LINE = (214, 205, 190)

T1 = T2 = T3 = 0.0
DUR = 1.0
TL = None
SHOTS = []
SUBS = []
BASE = None
PROPS = {}
SHOTS_IMG = {}
PREVIEW = "--preview" in sys.argv


# ---------------- 基础 ----------------
def make_bg():
    im = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        d.line([(0, y), (W, y)], fill=lerp_color(CREAM1, CREAM2, (y / H) ** 1.2))
    # 纸张纤维
    rng = random.Random(5)
    fib = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    fd = ImageDraw.Draw(fib)
    for _ in range(1400):
        x, y = rng.randint(0, W), rng.randint(0, H)
        fd.line([(x, y), (x + rng.randint(6, 40), y + rng.randint(-2, 2))],
                fill=(120, 100, 80, rng.randint(3, 9)))
    im = Image.alpha_composite(im.convert("RGBA"), fib)
    # 四角轻微压暗
    vig = Image.new("L", (W, H), 0)
    ImageDraw.Draw(vig).ellipse([-260, -180, W + 260, H + 180], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(200))
    inv = vig.point(lambda v: int((255 - v) * 0.28))
    return Image.composite(Image.new("RGB", (W, H), (226, 214, 198)), im.convert("RGB"), inv)


def card(img, x, y, w, h, r=18, fill=(255, 255, 255, 255), sh=0.55):
    paste_shadow(img, x, y, w, h, r, blur=26, alpha=int(150 * sh), dy=12)
    layer = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
    ImageDraw.Draw(layer).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=fill)
    img.alpha_composite(layer, (int(x), int(y)))


def place_prop(img, prop, cx, cy, maxw, maxh, zoom=1.0):
    w0, h0 = prop.size
    s = min(maxw / w0, maxh / h0) * zoom
    tw, th = int(w0 * s), int(h0 * s)
    im = prop.resize((tw, th), Image.Resampling.LANCZOS)
    x, y = cx - tw / 2, cy - th / 2
    paste_shadow(img, x, y, tw, th, 8, blur=22, alpha=95, dy=14)
    img.alpha_composite(im, (int(x), int(y)))
    return x, y, tw, th


def chip(img, x, y, text, size=26, fg=INK2, bg=(255, 255, 255, 240), border=LINE):
    w = text_w(text, size, "b") + 44
    h = size + 26
    layer = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h / 2, fill=bg, outline=border, width=1)
    d.text((w / 2, h / 2), text, font=font(size, "b"), fill=fg, anchor="mm")
    img.alpha_composite(layer, (int(x), int(y)))
    return w


def kicker(img, t):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 6], fill=(255, 255, 255, 120))
    d.rectangle([0, 0, W * clamp(t / DUR), 6], fill=ACC + (230,))
    chip(img, 56, 84, P.KICKER, 24, INK2, (255, 255, 255, 235), LINE)


# ---------------- 字幕 ----------------
def split_chunks(text, maxlen=17):
    parts = re.split(r"(?<=[，。；！？、])", text)
    out, cur = [], ""
    for p in parts:
        if not p:
            continue
        if cur and len(cur) + len(p) > maxlen:
            out.append(cur)
            cur = p
        else:
            cur += p
    if cur:
        out.append(cur)
    res = []
    for c in out:
        c = c.rstrip("，、；")
        res.append(c)
    return [c for c in res if c]


def hl_wrap(s):
    for w in sorted(P.HL_WORDS, key=len, reverse=True):
        i = s.find(w)
        if i >= 0:
            return s[:i] + "[[" + w + "]]" + s[i + len(w):]
    return s


def build_subs():
    subs = []
    for key in ("s1", "s2", "s3", "s4"):
        seg = TL[key]
        chunks = split_chunks(seg["text"] if "text" in seg else P.TEXT[key])
        total = sum(len(c) for c in chunks) or 1
        t = seg["start"]
        for c in chunks:
            d = seg["dur"] * len(c) / total
            subs.append((t, t + d, hl_wrap(c)))
            t += d
    return subs


def draw_subs(img, t):
    for s, e, txt in SUBS:
        if s <= t < e:
            p = clamp((t - s) / 0.22)
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            draw_rich(layer, txt, 1700 + int(14 * (1 - ease_out(p))), 46, max_w=940,
                      color=INK, hl_color=HL, weight="b", line_gap=1.32)
            if p < 1:
                a = layer.split()[3].point(lambda v: int(v * ease_out(p)))
                layer.putalpha(a)
            img.alpha_composite(layer)
            break


# ---------------- 场景 ----------------
def scene_open(img, lt, dur):
    p = clamp(lt / 0.8)
    rise = int(26 * (1 - ease_out(p)))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # 顶部竖线 + 小字
    d.line([56, 330, 56, 470], fill=ACC + (230,), width=5)
    d.text((88, 330), P.KICKER, font=font(28, "b"), fill=ACC + (255,))
    d.text((88, 378), "广告工程 · 经营管理", font=font(28), fill=MUTED + (255,))

    title_lines = getattr(P, "TITLE_LINES", [P.TITLE])
    y = 520 + rise
    for line in title_lines:
        d.text((56, y), line, font=font(94, "b"), fill=INK + (int(255 * ease_out(p)),))
        y += 118
    # 副标题
    d.text((58, y + 26), P.SUBTITLE, font=font(32), fill=INK2 + (int(255 * ease_out(p)),))
    # 手写式下划线
    d.line([58, y + 86, 58 + int(430 * ease_in_out(p)), y + 86], fill=ACC + (200,), width=4)
    img.alpha_composite(layer)
    # 底部三个小标签
    tags = ["Excel 台账", "一个客户一个文件夹", "月底对账"]
    x = 56
    for tg in tags:
        w = text_w(tg, 24, "b") + 40
        chip(img, x, 1080, tg, 24, INK2, (255, 255, 255, 210), LINE)
        x += w + 12


CHAOS = [
    ("folder", "一个客户一个文件夹", "翻到第几个了？", 1.0),
    ("order_excel", "报价、材料、人工全靠表格", "利润这一列，一直是 #REF!", 1.0),
    ("quote", "纸质报价单越堆越高", "同一单，报过三个价", 0.92),
    ("material", "料价三个版本，不知信哪个", "这个单价是去年的", 0.95),
    ("phone", "尾款问到微信里", "说到哪一笔了？", 0.86),
    ("notebook", "欠款记在本子上", "记得住吗？", 0.95),
]


def scene_chaos(img, lt, dur, idx):
    key, label, note, z = CHAOS[idx]
    prop = PROPS[key]
    p = clamp(lt / dur)
    zoom = lerp(1.0, 1.06, ease_in_out(p)) * z
    app = clamp((lt) / 0.45)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if app > 0:
        place_prop(layer, prop, W / 2, 900 - int(18 * (1 - ease_out(app))),
                   880, 940, zoom)
        a = layer.split()[3].point(lambda v: int(v * ease_out(app)))
        layer.putalpha(a)
        img.alpha_composite(layer)

    # 标签 + 批注
    if app > 0.4:
        p2 = clamp((lt - 0.35) / 0.4)
        chip(img, 56, 300, label, 26, INK2, (255, 255, 255, 240), LINE)
        if p2 > 0:
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(lay)
            a = int(255 * ease_out(p2))
            d.text((W / 2, 1470), note, font=font(38, "b"), fill=ACC + (a,), anchor="ma")
            d.line([W / 2 - 120, 1530, W / 2 + 120, 1530], fill=ACC + (int(a * 0.6),), width=3)
            img.alpha_composite(lay)


def scene_turn(img, lt, dur):
    p = clamp(lt / 0.7)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    # 卡片
    cy = 620
    cw, chh = 940, 420
    card(layer, (W - cw) / 2, cy, cw, chh, 26, (255, 255, 255, 250), 0.5)
    d.text((W / 2, cy + 96), "试了不少工具", font=font(40, "b"), fill=MUTED + (int(255 * p),), anchor="mm")
    d.text((W / 2, cy + 168), "都不贴合广告工程的流程", font=font(46, "b"), fill=INK + (int(255 * p),), anchor="mm")
    d.line([W / 2 - 300, cy + 232, W / 2 + 300, cy + 232], fill=LINE + (255,), width=2)
    p2 = clamp((lt - 1.6) / 0.7)
    if p2 > 0:
        d.text((W / 2, cy + 300), "直到用上一款管理软件", font=font(52, "b"),
               fill=(INK[0], INK[1], INK[2], int(255 * ease_out(p2))), anchor="mm")
        w = int(360 * ease_out(p2))
        d.line([W / 2 - w / 2, cy + 352, W / 2 + w / 2, cy + 352], fill=ACC + (220,), width=8)
    img.alpha_composite(layer)


def scene_screen(img, lt, dur, idx):
    name, fn, note = P.SCREENS[idx]
    p = clamp(lt / 0.45)
    src = SHOTS_IMG[fn]
    cw, chh = 940, 528
    x, y = (W - cw) / 2, 470
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p2 = clamp(lt / dur)
    zoom = lerp(1.0, 1.035, ease_in_out(p2))
    s = cw / src.width * zoom
    sw, sh = cw / s, chh / s
    box = ((src.width - sw) / 2, (src.height - sh) / 2, (src.width + sw) / 2, (src.height + sh) / 2)
    shot = src.crop(tuple(int(v) for v in box)).resize((cw, chh), Image.Resampling.LANCZOS)
    card(layer, x, y, cw, chh, 16, (255, 255, 255, 255), 0.55)
    mask = Image.new("L", (cw, chh), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, cw - 1, chh - 1], radius=16, fill=255)
    layer.paste(shot, (int(x), int(y)), mask)
    a = layer.split()[3].point(lambda v: int(v * ease_out(p)))
    layer.putalpha(a)
    img.alpha_composite(layer)

    if p > 0.5:
        d = ImageDraw.Draw(img)
        d.text((56, 300), name, font=font(46, "b"), fill=INK)
        d.text((56, 372), note, font=font(30), fill=INK2)
        # 流程条
        fy = 1090
        xs = []
        total = sum(text_w(f, 26, "b") + 52 for f in P.FLOW) + 34 * (len(P.FLOW) - 1)
        cx = (W - total) / 2
        act = P.SCREEN_FLOW[idx]
        for i, f in enumerate(P.FLOW):
            wf = text_w(f, 26, "b") + 52
            active = (i == act)
            lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            dd = ImageDraw.Draw(lay)
            dd.rounded_rectangle([cx, fy, cx + wf, fy + 62], radius=31,
                                 fill=(28, 86, 214, 235) if active else (255, 255, 255, 235),
                                 outline=None if active else LINE, width=1)
            dd.text((cx + wf / 2, fy + 31), f, font=font(26, "b"),
                    fill=(255, 255, 255) if active else INK2, anchor="mm")
            img.alpha_composite(lay)
            xs.append((cx, cx + wf))
            cx += wf
            if i < len(P.FLOW) - 1:
                d.line([cx + 6, fy + 31, cx + 28, fy + 31], fill=MUTED + (255,), width=2)
                cx += 34


def scene_close(img, lt, dur):
    p = clamp(lt / 0.8)
    rise = int(24 * (1 - ease_out(p)))
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    a = int(255 * ease_out(p))
    d.text((W / 2, 520 + rise), P.END_MAIN, font=font(64, "b"), fill=INK + (a,), anchor="mm")
    d.text((W / 2, 610 + rise), P.END_SUB, font=font(40), fill=INK2 + (a,), anchor="mm")
    # 分隔
    d.line([W / 2 - 180, 676 + rise, W / 2 + 180, 676 + rise], fill=ACC + (int(a * 0.8),), width=4)
    # 提问条
    p2 = clamp((lt - 1.2) / 0.7)
    if p2 > 0:
        cw, chh = 920, 150
        card(layer, (W - cw) / 2, 760 + rise, cw, chh, 24, (255, 255, 255, 250), 0.45)
        d.text((W / 2, 760 + rise + 62), P.END_ASK, font=font(38, "b"),
               fill=INK + (int(255 * ease_out(p2)),), anchor="mm")
        d.text((W / 2, 760 + rise + 112), "你的台账现在是怎么管的？", font=font(28),
               fill=MUTED + (int(255 * ease_out(p2)),), anchor="mm")
    # 向下箭头
    p3 = clamp((lt - 2.2) / 0.6)
    if p3 > 0:
        ay = 1010 + rise + int(10 * math.sin(lt * 2))
        col = ACC + (int(200 * ease_out(p3)),)
        d.line([W / 2, ay, W / 2, ay + 40], fill=col, width=5)
        d.line([W / 2 - 16, ay + 26, W / 2, ay + 46], fill=col, width=5)
        d.line([W / 2 + 16, ay + 26, W / 2, ay + 46], fill=col, width=5)
    d.text((W / 2, 1300), P.SIGN, font=font(26), fill=MUTED + (a,), anchor="mm")
    img.alpha_composite(layer)


# ---------------- 组装 ----------------
def init_assets():
    global T1, T2, T3, DUR, TL, SUBS, BASE, PROPS, SHOTS
    with open(TIMELINE, encoding="utf-8") as f:
        TL = json.load(f)
    T1 = TL["s2"]["start"] - 0.35
    T2 = TL["s3"]["start"] - 0.35
    T3 = TL["s4"]["start"] - 0.35
    DUR = TL["total"]
    for k in ("s1", "s2", "s3", "s4"):
        TL[k]["text"] = P.TEXT[k]
    SUBS = build_subs()
    BASE = make_bg().convert("RGBA")

    PROPS["folder"] = make_folder_window()
    PROPS["order_excel"] = make_order_excel()
    PROPS["quote"] = make_quote_sheet(101, 940, 1240, "门头工程报价单")
    PROPS["material"] = make_material_sheet(103, 1040, 780)
    PROPS["phone"] = make_phone(105, title="王总 · 门头工程", msgs=[
        ("left", "上次那单尾款，\n这周给你结"),
        ("right", "好的王总，我把单子\n找出来对一下"),
        ("left", "你那边一共欠多少？"),
        ("right", "我翻下文件夹……"),
        ("left", "不急，你先理清楚"),
    ])
    PROPS["notebook"] = make_notebook(107, 460, 600, "欠款记录", (58, 92, 132))

    for name, fn, note in P.SCREENS:
        SHOTS_IMG[fn] = Image.open(os.path.join(SHOT_DIR, fn)).convert("RGB")

    shots = [("open", 0.0, 6.0, None)]
    a0 = T1 - 6.0
    p1 = [0, 1, 2, 3]
    step = a0 / len(p1)
    for i, pi in enumerate(p1):
        shots.append(("chaos", 6.0 + i * step, 6.0 + (i + 1) * step, pi))
    turn_start = max(T1 + 8.0, T2 - 7.2)
    b = turn_start - T1
    p2 = [4, 5]
    step2 = b / len(p2)
    for i, pi in enumerate(p2):
        shots.append(("chaos", T1 + i * step2, T1 + (i + 1) * step2, pi))
    shots.append(("turn", turn_start, T2, None))
    c = (T3 - T2) / len(P.SCREENS)
    for i in range(len(P.SCREENS)):
        shots.append(("screen", T2 + i * c, T2 + (i + 1) * c, i))
    shots.append(("close", T3, DUR, None))
    SHOTS = shots


def render_frame(t):
    img = BASE.copy()
    cur = SHOTS[-1]
    for sh in SHOTS:
        if sh[1] <= t < sh[2]:
            cur = sh
            break
    kind, t0, t1, payload = cur
    lt = t - t0
    dur = max(0.2, t1 - t0)
    if kind == "open":
        scene_open(img, lt, dur)
    elif kind == "chaos":
        scene_chaos(img, lt, dur, payload)
    elif kind == "turn":
        # 从上一个镜头淡入
        scene_turn(img, lt, dur)
    elif kind == "screen":
        scene_screen(img, lt, dur, payload)
    else:
        scene_close(img, lt, dur)
    kicker(img, t)
    draw_subs(img, t)
    return img.convert("RGB")


def main():
    init_assets()
    if PREVIEW:
        for s in sys.argv:
            if s.startswith("--t="):
                tt = float(s.split("=")[1])
                render_frame(tt).save(os.path.join(VID, f"preview_adstory_{tt:05.1f}.png"))
        print("preview ok")
        return
    ff = __import__("imageio_ffmpeg").get_ffmpeg_exe()
    cmd = [ff, "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-"]
    if os.path.exists(MASTER):
        cmd += ["-i", MASTER]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
            "-profile:v", "high", "-movflags", "+faststart"]
    if os.path.exists(MASTER):
        cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += [OUT]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    total = int(round(DUR * FPS))
    for i in range(total):
        proc.stdin.write(render_frame(i / FPS).tobytes())
        if i % 200 == 0:
            print(f"frame {i}/{total}", flush=True)
    proc.stdin.close()
    err = proc.stderr.read().decode("utf-8", "ignore")
    proc.wait()
    open(os.path.join(VID, "ffmpeg_story.txt"), "w", encoding="utf-8").write(err[-2000:])
    print("done", OUT, DUR)


if __name__ == "__main__":
    main()
