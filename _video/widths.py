# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import vrender as R
from vdraw import text_w

lines = []
lines.append(f"URL@36 = {text_w(R.OFFICIAL, 36, 'b'):.0f}  (limit 958)")
lines.append(f"PHONE@100 = {text_w(R.PHONE, 100, 'b'):.0f}  (limit 1000)")
lines.append(f"SLOGAN@40 = {text_w('物管通 —— 让物业的账和事，清清楚楚！', 40, 'b'):.0f}  (limit 1000)")
lines.append(f"TITLE@66 = {text_w('物管通 EstatePilot', 66, 'b'):.0f}")
for i, ws in enumerate(R.KEYWORDS):
    widths = [text_w(w, 30, "b") + 46 for w in ws]
    tot = sum(widths) + 14 * (len(ws) - 1)
    lines.append(f"kw{i+1} total={tot:.0f}")
for i, (t, fn, note, tg) in enumerate(R.SCREENS):
    lines.append(f"screen{i+1} title={text_w(t.split(' ',1)[1], 52, 'b'):.0f} note={text_w(note, 31):.0f}")
open(os.path.join(R.VID, "widths.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("ok")
