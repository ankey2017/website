# -*- coding: utf-8 -*-
"""把 master.wav 做一次柔和的响度提升（幂曲线 + 峰值归一），原文件备份为 master_raw.wav"""
import os, wave, shutil
import numpy as np

VID = r"E:\vscode\zhouji\webHome\_video"
src = os.path.join(VID, "master.wav")
raw = os.path.join(VID, "master_raw.wav")
if not os.path.exists(raw):
    shutil.copy2(src, raw)

with wave.open(raw, "rb") as w:
    sr, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
    data = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
data = data.reshape(-1, ch)
x = np.sign(data) * (np.abs(data) ** 0.88)
x = x / (np.max(np.abs(x)) + 1e-9) * 0.95
pcm = (np.clip(x, -1, 1) * 32767).astype(np.int16)
with wave.open(src, "wb") as w:
    w.setnchannels(ch)
    w.setsampwidth(sw)
    w.setframerate(sr)
    w.writeframes(pcm.tobytes())

rms = np.sqrt(np.mean(x ** 2))
open(os.path.join(VID, "loudness.txt"), "w", encoding="utf-8").write(
    f"peak={np.max(np.abs(x)):.3f} rms_db={20*np.log10(rms+1e-9):.1f}")
print("ok")
