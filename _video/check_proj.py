# -*- coding: utf-8 -*-
"""关键帧体检（按 VP 项目筛选）"""
import os, glob, sys
import numpy as np
from PIL import Image

PROJ = os.environ.get("VP", "estate")
VID = r"E:\vscode\zhouji\webHome\_video"
bands = [("top", 0, 320), ("card", 320, 1060), ("below", 1060, 1400),
         ("subtitle", 1520, 1800), ("footer", 1800, 1920)]
lines = []
for p in sorted(glob.glob(os.path.join(VID, f"preview_{PROJ}_*.png"))):
    a = np.asarray(Image.open(p).convert("L"), dtype=np.float32)
    lines.append(f"== {os.path.basename(p)} mean={a.mean():.1f}")
    for name, y0, y1 in bands:
        b = a[y0:y1]
        lines.append(f"   {name:9s}: mean={b.mean():5.1f} bright%={(b>200).mean()*100:5.2f} std={b.std():5.1f}")
open(os.path.join(VID, f"frame_check_{PROJ}.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("ok")
