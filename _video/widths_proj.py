# -*- coding: utf-8 -*-
"""排版宽度体检：确认各段文字不会超界或挤压（按 VP 环境变量选项目）"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from vdraw import text_w

PROJ = os.environ.get("VP", "estate")
P = __import__("project_" + PROJ)

lines = [f"project={PROJ}"]
us = 36
while text_w(P.OFFICIAL, us, "b") > 958 and us > 20:
    us -= 1
lines.append(f"URL 自适应字号={us}px 宽={text_w(P.OFFICIAL, us, 'b'):.0f} (限 958)")
lines.append(f"SLOGAN@40={text_w(P.SLOGAN, 40, 'b'):.0f} (限 1000)")
lines.append(f"标题@66={text_w(P.NAME + ' ' + P.NAME_EN, 66, 'b'):.0f} (限 1000)")
for i, ws in enumerate(P.KEYWORDS):
    tot = sum(text_w(w, 30, "b") + 46 for w in ws) + 14 * (len(ws) - 1)
    lines.append(f"关键词{i+1}: {tot:.0f}")
for i, (t, fn, note, tg) in enumerate(P.SCREENS):
    lines.append(f"屏{i+1} 标题={text_w(t.split(' ', 1)[1], 52, 'b'):.0f} 说明={text_w(note, 31):.0f} (限 960)")
for i, c in enumerate(P.CHIPS):
    lines.append(f"适配块{i+1} '{c}' = {text_w(c, 36, 'b') + 76:.0f} (限 470)")
for name, desc, hi in P.ROWS:
    nw = text_w(name, 37, "b")
    dw = text_w(desc, 29, "b")
    lines.append(f"对比行 '{name}' 左={104 + nw:.0f} 右起={996 - dw:.0f} 间隙={996 - dw - 104 - nw:.0f}")
for i, s in enumerate(P.DEMO_SUBS):
    plain = s.replace("[[", "").replace("]]", "")
    lines.append(f"演示字幕{i+1} 宽≈{text_w(plain, 45, 'b'):.0f} (限 950，超出会自动换行)")
open(os.path.join(os.path.dirname(__file__), f"widths_{PROJ}.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("ok")
