# -*- coding: utf-8 -*-
"""对比两条片子的 BGM：取尾段纯音乐区间做频谱，确认版本不同"""
import os, wave
import numpy as np

VID = r"E:\vscode\zhouji\webHome\_video"
lines = []
for name in ("master_estate.wav", "master_asset.wav", "master_livesell.wav", "master_stock.wav", "master_code.wav"):
    p = os.path.join(VID, name)
    if not os.path.exists(p):
        lines.append(f"{name} 不存在")
        continue
    with wave.open(p, "rb") as w:
        sr = w.getframerate()
        d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
        d = d.reshape(-1, 2).mean(axis=1)
    # 取倒数 3.0~6.5 秒（只有 BGM）
    seg = d[int((len(d) / sr - 6.5) * sr): int((len(d) / sr - 3.0) * sr)]
    spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
    freqs = np.fft.rfftfreq(len(seg), 1 / sr)
    low = (freqs > 80) & (freqs < 900)
    idx = np.argsort(spec[low])[-4:][::-1]
    peaks = [f"{freqs[low][i]:.0f}Hz" for i in idx]
    centroid = float(np.sum(freqs * spec) / (np.sum(spec) + 1e-9))
    lines.append(f"{name}: rms={np.sqrt(np.mean(seg**2)):.4f} 主峰={' '.join(peaks)} 谱心={centroid:.0f}Hz")
open(os.path.join(VID, "bgm_compare.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("ok")
