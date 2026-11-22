# -*- coding: utf-8 -*-
import os, wave, subprocess
import numpy as np
import imageio_ffmpeg

VID = r"E:\vscode\zhouji\webHome\_video"
FF = imageio_ffmpeg.get_ffmpeg_exe()
lines = []

# ---- 音频 ----
with wave.open(os.path.join(VID, "master.wav"), "rb") as w:
    sr = w.getframerate()
    d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
    d = d.reshape(-1, 2).mean(axis=1)
lines.append(f"audio dur={len(d)/sr:.2f}s peak={np.max(np.abs(d)):.3f}")
for i in range(0, int(len(d) / sr), 4):
    seg = d[i * sr:(i + 4) * sr]
    rms = np.sqrt(np.mean(seg ** 2))
    lines.append(f"  {i:>2}-{i+4:<2}s rms={rms:.4f} db={20*np.log10(rms+1e-9):.1f}")

# ---- 视频：每秒一帧的亮度 ----
tmp = os.path.join(VID, "qc")
os.makedirs(tmp, exist_ok=True)
for f in os.listdir(tmp):
    os.remove(os.path.join(tmp, f))
subprocess.run([FF, "-y", "-loglevel", "error", "-i", os.path.join(VID, "wuguantong_promo.mp4"),
                "-vf", "fps=1,scale=180:320", os.path.join(tmp, "%03d.png")], check=True)
from PIL import Image
means = []
for i, fn in enumerate(sorted(os.listdir(tmp))):
    a = np.asarray(Image.open(os.path.join(tmp, fn)).convert("L"), dtype=np.float32)
    means.append(a.mean())
lines.append("video 1fps mean brightness: " + " ".join(f"{m:.0f}" for m in means))
open(os.path.join(VID, "qc_report.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("ok")
