# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np
from PIL import Image
import vrender as R

R.init_assets()
for t in (46.0, 52.0, 57.0):
    img = R.render_frame(t)
    a = np.asarray(img.convert("L"), dtype=np.float32)
    out = [f"t={t} mean={a.mean():.1f}"]
    for y0 in range(800, 1320, 108):
        band = a[y0:y0 + 60, :]
        out.append(f"  y{y0}-{y0+60} max={band.max():.0f} bright%={(band>200).mean()*100:.2f}")
    open(os.path.join(R.VID, f"dbg_{int(t)}.txt"), "w", encoding="utf-8").write("\n".join(out))
print("ok")
