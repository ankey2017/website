# -*- coding: utf-8 -*-
"""经验分享片关键帧体检：浅色主题下看暗像素（文字/卡片）分布"""
import os, glob
import numpy as np
from PIL import Image

VID = r"E:\vscode\zhouji\webHome\_video"
bands = [("kicker", 60, 200), ("title", 280, 800), ("card", 800, 1400),
         ("note", 1400, 1560), ("subs", 1600, 1820)]
lines = []
for p in sorted(glob.glob(os.path.join(VID, "preview_adstory_*.png"))):
    a = np.asarray(Image.open(p).convert("L"), dtype=np.float32)
    lines.append(f"== {os.path.basename(p)} mean={a.mean():.0f} dark%={(a<90).mean()*100:.2f}")
    for name, y0, y1 in bands:
        b = a[y0:y1]
        lines.append(f"   {name:7s} mean={b.mean():5.0f} dark%={(b<90).mean()*100:5.2f} std={b.std():5.1f}")
open(os.path.join(VID, "frame_check_adstory.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("ok")
