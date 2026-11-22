# -*- coding: utf-8 -*-
"""关键帧体检：统计各区域像素分布，用于无视觉反馈时确认排版没有空/挤"""
import os, glob
import numpy as np
from PIL import Image

VID = r"E:\vscode\zhouji\webHome\_video"
bands = [("top", 0, 320), ("card", 320, 1060), ("below", 1060, 1400),
         ("subtitle", 1520, 1800), ("footer", 1800, 1920)]
lines = []
for p in sorted(glob.glob(os.path.join(VID, "preview_*.png"))):
    im = Image.open(p).convert("L")
    a = np.asarray(im, dtype=np.float32)
    lines.append(f"== {os.path.basename(p)}  mean={a.mean():.1f}")
    for name, y0, y1 in bands:
        b = a[y0:y1]
        bright = (b > 200).mean() * 100
        lines.append(f"   {name:9s} y{y0}-{y1}: mean={b.mean():5.1f} bright%={bright:5.2f} std={b.std():5.1f}")
    # 极右边缘是否被裁（右侧 12px 应有背景）
    edge = a[:, -12:].mean()
    lines.append(f"   right-edge mean={edge:.1f}")
open(os.path.join(VID, "frame_check.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("ok")
