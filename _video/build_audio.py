# -*- coding: utf-8 -*-
"""生成旁白（全本，自适应语速使总片长约 60~62s）+ 背景音乐 + 音效 -> master.wav / timeline.json"""
import asyncio, os, json, subprocess, wave, math
import numpy as np
import imageio_ffmpeg
import edge_tts

ROOT = r"E:\vscode\zhouji\webHome\_video"
AUD = os.path.join(ROOT, "audio")
os.makedirs(AUD, exist_ok=True)
FF = imageio_ffmpeg.get_ffmpeg_exe()
VOICE = "zh-CN-YunjianNeural"
SR = 44100

PROJ = os.environ.get("VP", "estate").strip() or "estate"
P = __import__("project_" + PROJ)
TEXT = P.TEXT
OUT_MASTER = os.path.join(ROOT, f"master_{PROJ}.wav")
OUT_TIMELINE = os.path.join(ROOT, f"timeline_{PROJ}.json")

PAD0, GAP, PAD3, POSTER = 0.35, 0.45, 0.55, getattr(P, "TAIL", 7.0)
TARGET_TOTAL_MAX = getattr(P, "MAX_TOTAL", 62.0)


def wav_dur(p):
    with wave.open(p, "rb") as w:
        return w.getnframes() / float(w.getframerate())


def load_wav(p):
    with wave.open(p, "rb") as w:
        n = w.getnframes()
        d = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
        if w.getnchannels() == 2:
            d = d.reshape(-1, 2).mean(axis=1)
    return d


async def synth(key, rate, tag):
    mp3 = os.path.join(AUD, f"{PROJ}_{key}_{tag}.mp3")
    wav = os.path.join(AUD, f"{PROJ}_{key}_{tag}.wav")
    await edge_tts.Communicate(TEXT[key], VOICE, rate=rate).save(mp3)
    subprocess.run([FF, "-y", "-loglevel", "error", "-i", mp3, "-ar", str(SR), "-ac", "1", wav], check=True)
    return wav, wav_dur(wav)


async def measure(rate, tag):
    keys = ("s1", "s2", "s3", "s4")
    res = await asyncio.gather(*[synth(k, rate, tag) for k in keys])
    return dict(zip(keys, res))


async def pick():
    log = []
    d0 = await measure("+18%", "a18")
    s = d0["s1"][1] + d0["s2"][1] + d0["s3"][1]
    budget = TARGET_TOTAL_MAX - PAD0 - 2 * GAP - PAD3 - POSTER
    log.append(f"@+18% speech(s1+s2+s3)={s:.2f}s budget={budget:.2f}s")
    need = 1.18 * s / budget
    r = max(0.05, min(0.45, need - 1))
    r = round(r * 50) / 50
    log.append(f"target rate={r:+.0%}")
    tag = f"r{int(round(r * 100))}"
    chosen = await measure(f"+{int(round(r * 100))}%", tag)
    s = chosen["s1"][1] + chosen["s2"][1] + chosen["s3"][1]
    log.append(f"@+{int(round(r*100))}% speech={s:.2f}s")
    for _ in range(2):
        if s <= budget:
            break
        r = round((r + 0.03) * 50) / 50
        tag = f"r{int(round(r * 100))}"
        chosen = await measure(f"+{int(round(r * 100))}%", tag)
        s = chosen["s1"][1] + chosen["s2"][1] + chosen["s3"][1]
        log.append(f"retry @+{int(round(r*100))}% speech={s:.2f}s")

    d = {k: chosen[k][1] for k in ("s1", "s2", "s3", "s4")}
    t1 = PAD0
    t2 = t1 + d["s1"] + GAP
    t3 = t2 + d["s2"] + GAP
    t4 = t3 + d["s3"] + PAD3
    total = t4 + max(POSTER, d["s4"] + 2.0)
    total = round(total + 0.25, 2)  # 尾部留一点余量

    tl = {
        "total": total,
        "rate": f"+{int(round(r*100))}%",
        "s1": {"start": round(t1, 2), "end": round(t1 + d["s1"], 2), "dur": round(d["s1"], 2), "wav": chosen["s1"][0]},
        "s2": {"start": round(t2, 2), "end": round(t2 + d["s2"], 2), "dur": round(d["s2"], 2), "wav": chosen["s2"][0]},
        "s3": {"start": round(t3, 2), "end": round(t3 + d["s3"], 2), "dur": round(d["s3"], 2), "wav": chosen["s3"][0]},
        "s4": {"start": round(t4, 2), "end": round(t4 + d["s4"], 2), "dur": round(d["s4"], 2), "wav": chosen["s4"][0]},
    }
    log.append("total=%.2fs" % total)
    return tl, log


# ---------------- 音乐 ----------------
def box_smooth(x, k):
    if k <= 1:
        return x
    c = np.cumsum(np.concatenate([[0.0], x]))
    y = (c[k:] - c[:-k]) / k
    pad = np.full(k - 1, y[-1] if len(y) else 0.0)
    return np.concatenate([y, pad])[: len(x)]


def env_adsr(n, a, dly, s, r, sr=SR):
    a_n, d_n, r_n = int(a * sr), int(dly * sr), int(r * sr)
    s_n = max(0, n - a_n - d_n - r_n)
    parts = []
    if a_n:
        parts.append(np.linspace(0, 1, a_n, endpoint=False))
    if d_n:
        parts.append(np.linspace(1, s, d_n, endpoint=False))
    parts.append(np.full(s_n, s))
    if r_n:
        parts.append(np.linspace(s, 0, r_n))
    e = np.concatenate(parts)
    if len(e) < n:
        e = np.pad(e, (0, n - len(e)))
    return e[:n]


def note_hz(m):
    return 440.0 * 2 ** ((m - 69) / 12.0)


BGM_PRESETS = {
    # a：稍明快，Am7-F-C-G，主打“商务科技”
    "a": dict(
        chords=[[57, 60, 64, 67], [53, 57, 60, 64], [48, 55, 59, 64], [55, 59, 62, 64]],
        bpm=90, pad_amp=0.082, harm=0.18, pad_atk=1.0,
        pluck=(0.050, 0.034), decay=7.5, kick=0.070, air=0.014, bell=0.0,
    ),
    # b：更慢更暖，Dm7-G-Cmaj7-Am7，少打击感、多一层高音泛音垫
    "b": dict(
        chords=[[50, 53, 57, 60], [55, 58, 62, 65], [48, 52, 55, 59], [57, 60, 64, 67]],
        bpm=78, pad_amp=0.090, harm=0.09, pad_atk=1.8,
        pluck=(0.040, 0.026), decay=5.4, kick=0.042, air=0.017, bell=0.016,
    ),
    # c：轻快有节奏，C-G-Am-F 流行进行，适合直播带货的活泼调性
    "c": dict(
        chords=[[48, 52, 55, 60], [55, 59, 62, 67], [57, 60, 64, 69], [53, 57, 60, 65]],
        bpm=102, pad_amp=0.070, harm=0.14, pad_atk=0.7,
        pluck=(0.056, 0.030), decay=8.2, kick=0.085, air=0.012, bell=0.0,
    ),
    # d：朴实温和，F-Dm-Bb-C，节奏像计数器一样匀，适合仓储/日常经营
    "d": dict(
        chords=[[53, 57, 60, 65], [50, 53, 57, 62], [46, 50, 53, 58], [48, 52, 55, 60]],
        bpm=86, pad_amp=0.078, harm=0.11, pad_atk=1.1,
        pluck=(0.046, 0.028), decay=6.8, kick=0.058, air=0.015, bell=0.008,
    ),
    # e：轻巧跳跃，G-Em-C-D，短促琶音像“咔哒咔哒”打标签，适合小工具
    "e": dict(
        chords=[[55, 59, 62, 67], [52, 55, 59, 64], [48, 52, 55, 60], [50, 54, 57, 62]],
        bpm=96, pad_amp=0.066, harm=0.16, pad_atk=0.5,
        pluck=(0.058, 0.038), decay=11.0, kick=0.062, air=0.011, bell=0.012,
    ),
}


def make_bgm(dur, variant="a"):
    cfg = BGM_PRESETS.get(variant, BGM_PRESETS["a"])
    chords = cfg["chords"]
    beat = 60.0 / cfg["bpm"]
    n = int(dur * SR)
    out = np.zeros(n)
    chord_len = beat * 8
    for i in range(int(math.ceil(dur / chord_len)) + 1):
        st = i * chord_len
        if st >= dur:
            break
        seg_n = int(min(chord_len + 1.6, dur - st) * SR)
        if seg_n <= 100:
            continue
        seg_t = np.arange(seg_n) / SR
        e = env_adsr(seg_n, cfg["pad_atk"], 0.3, 0.82, 1.3)
        buf = np.zeros(seg_n)
        for j, m in enumerate(chords[i % 4]):
            f = note_hz(m + 12)
            buf += 0.85 * np.sin(2 * np.pi * f * (1 + (j - 1.5) * 0.0008) * seg_t + j)
            buf += cfg["harm"] * np.sin(2 * np.pi * f * 2 * seg_t + j * 0.6)
        buf *= e * cfg["pad_amp"]
        idx = np.arange(seg_n) + int(st * SR)
        m_ = idx < n
        out[idx[m_]] += buf[m_]

        # b 版：每和弦垫一层很轻的高音泛音
        if cfg["bell"] > 0:
            f = note_hz(chords[i % 4][0] + 24)
            seg_n2 = int(min(chord_len + 2.0, dur - st) * SR)
            t2 = np.arange(seg_n2) / SR
            env2 = np.clip(t2 / 1.5, 0, 1) * np.exp(-t2 * 3.2)
            b2 = np.sin(2 * np.pi * f * t2) * env2 * cfg["bell"]
            idx2 = np.arange(seg_n2) + int(st * SR)
            m2 = idx2 < n
            out[idx2[m2]] += b2[m2]

    step = beat / 2
    k = 0
    while k * step < dur - 0.2:
        st = k * step
        c = chords[int(st // chord_len) % 4]
        f = note_hz(c[k % len(c)] + 12)
        seg_n = int(0.55 * SR)
        t = np.arange(seg_n) / SR
        amp = cfg["pluck"][0] if k % 2 == 0 else cfg["pluck"][1]
        buf = (np.sin(2 * np.pi * f * t) * 0.8 + np.sin(2 * np.pi * f * 2 * t) * 0.12) * np.exp(-t * cfg["decay"]) * amp
        idx = np.arange(seg_n) + int(st * SR)
        m_ = idx < n
        out[idx[m_]] += buf[m_]
        k += 1

    bi = 0
    while bi * beat < dur - 0.3:
        if bi % 4 in (0, 2):
            st = bi * beat
            seg_n = int(0.30 * SR)
            t = np.arange(seg_n) / SR
            buf = np.sin(2 * np.pi * 58 * t) * np.exp(-t * 16) * cfg["kick"]
            idx = np.arange(seg_n) + int(st * SR)
            m_ = idx < n
            out[idx[m_]] += buf[m_]
        bi += 1

    rng = np.random.default_rng(7)
    air = rng.normal(0, 1, n)
    for _ in range(2):
        air = box_smooth(air, 320)
    air = air / (np.max(np.abs(air)) + 1e-9)
    out += air * cfg["air"]

    fi = int(1.4 * SR)
    out[:fi] *= np.linspace(0, 1, fi)
    fo = int(2.6 * SR)
    out[-fo:] *= np.linspace(1, 0, fo)
    return out


def fx_click():
    n = int(0.09 * SR)
    t = np.arange(n) / SR
    noise = np.random.default_rng(3).normal(0, 1, n) * np.exp(-t * 230)
    ping = np.sin(2 * np.pi * 1750 * t) * np.exp(-t * 55) * 0.5 + np.sin(2 * np.pi * 900 * t) * np.exp(-t * 70) * 0.3
    return (noise * 0.3 + ping) * 0.45


def fx_pop():
    n = int(0.15 * SR)
    t = np.arange(n) / SR
    f = 760 * np.exp(-t * 9) + 320
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 22) * 0.3


def fx_whoosh():
    n = int(0.8 * SR)
    t = np.arange(n) / SR
    noise = np.random.default_rng(11).normal(0, 1, n)
    lo = box_smooth(noise, 260)
    mid = box_smooth(noise, 60)
    y = mid - lo
    env = np.sin(np.pi * np.clip(t / t[-1], 0, 1)) ** 2
    y = y / (np.max(np.abs(y)) + 1e-9)
    return y * env * 0.2


def place(dst, src, at, gain=1.0):
    i = int(at * SR)
    if i >= len(dst):
        return
    m = min(len(src), len(dst) - i)
    dst[i:i + m] += src[:m] * gain


def build_mix(tl):
    dur = tl["total"]
    n = int(dur * SR)
    nar = np.zeros(n)
    for k in ("s1", "s2", "s3", "s4"):
        seg = load_wav(tl[k]["wav"])
        seg = seg / (np.max(np.abs(seg)) + 1e-9) * 0.88
        place(nar, seg, tl[k]["start"])

    bgm = make_bgm(dur, getattr(P, "BGM", "a"))
    bgm = bgm / (np.max(np.abs(bgm)) + 1e-9) * 0.15
    env = box_smooth(np.abs(nar), int(0.25 * SR))
    env = np.clip(env / 0.18, 0, 1)
    bgm *= (1.0 - 0.38 * env)

    sfx = np.zeros(n)
    for key in ("s2", "s3", "s4"):
        place(sfx, fx_whoosh(), tl[key]["start"] - 0.42, 0.5)
    s2s, s2d = tl["s2"]["start"], tl["s2"]["dur"]
    for i in range(9):
        at = s2s + i * (s2d / 9) + 0.66
        place(sfx, fx_click(), at, 0.42)
        place(sfx, fx_click(), at + 0.44, 0.28)
    for at in (tl["s1"]["start"], tl["s3"]["start"], tl["s4"]["start"]):
        place(sfx, fx_pop(), at, 0.3)

    mix = nar + bgm + sfx
    mix = np.sign(mix) * (np.abs(mix) ** 0.88)
    mix = mix / (np.max(np.abs(mix)) + 1e-9) * 0.95

    d = int(0.008 * SR)
    right = mix.copy()
    right[d:] = mix[:-d]
    st = np.stack([mix, right], axis=1)
    pcm = (np.clip(st, -1, 1) * 32767).astype(np.int16)
    out = OUT_MASTER
    with wave.open(out, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return out


async def main():
    tl, log = await pick()
    wav = build_mix(tl)
    log.append("wav " + wav)
    with open(OUT_TIMELINE, "w", encoding="utf-8") as f:
        json.dump(tl, f, ensure_ascii=False, indent=2)
    with open(os.path.join(ROOT, f"audio_report_{PROJ}.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(log))
    print("ok")


asyncio.run(main())
