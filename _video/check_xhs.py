# -*- coding: utf-8 -*-
"""小红书专版收尾检查：确认无官网/电话残留（看纵向分布 + 逐步出现的元素）"""
import os, glob
import numpy as np
from PIL import Image

VID = r"E:\vscode\zhouji\webHome\_video"
bands = [("logo", 180, 460), ("name", 480, 620), ("slogan", 640, 740),
         ("ask", 820, 1140), ("chips", 1180, 1290), ("follow", 1350, 1410),
         ("bottom", 1700, 1790)]
lines = []
for p in sorted(glob.glob(os.path.join(VID, "preview_assetxhs_*.png"))):
    a = np.asarray(Image.open(p).convert("L"), dtype=np.float32)
    lines.append(f"== {os.path.basename(p)} mean={a.mean():.0f}")
    for name, y0, y1 in bands:
        b = a[y0:y1]
        lines.append(f"   {name:7s} mean={b.mean():5.0f} bright%={(b>190).mean()*100:5.2f}")
    # 旧版官网/电话区域（y 750~1160 曾经是 URL+电话），这里应该只有提问卡
    old = a[940:1170]
    lines.append(f"   [旧URL+电话区] mean={old.mean():.0f} bright%={(old>190).mean()*100:.2f}")
open(os.path.join(VID, "frame_check_xhs.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("ok")
