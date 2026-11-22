# -*- coding: utf-8 -*-
"""成片 QC：每秒亮度曲线（确认段落切换、没有黑屏/冻结）"""
import os, glob
import numpy as np
import subprocess
import imageio_ffmpeg
from PIL import Image

PROJ = os.environ.get("VP", "crm")
VID = r"E:\vscode\zhouji\webHome\_video"
SRC = os.path.join(VID, f"promo_{PROJ}.mp4")
FF = imageio_ffmpeg.get_ffmpeg_exe()
tmp = os.path.join(VID, f"qc_{PROJ}")
os.makedirs(tmp, exist_ok=True)
for f in os.listdir(tmp):
    os.remove(os.path.join(tmp, f))
subprocess.run([FF, "-y", "-loglevel", "error", "-i", SRC, "-vf", "fps=1,scale=180:320",
                os.path.join(tmp, "%03d.png")], check=True)
means = []
for fn in sorted(os.listdir(tmp)):
    a = np.asarray(Image.open(os.path.join(tmp, fn)).convert("L"), dtype=np.float32)
    means.append(a.mean())
open(os.path.join(VID, f"qc_{PROJ}.txt"), "w", encoding="utf-8").write(
    f"{PROJ} 1fps mean brightness:\n" + " ".join(f"{m:.0f}" for m in means))
print("ok")
