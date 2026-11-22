# -*- coding: utf-8 -*-
"""素材冒烟测试：只生成三张 B-roll 与纸张素材，方便检查观感"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import vrender as R

shots = R.build_broll()
for i, s in enumerate(shots):
    s.convert("RGB").resize((540, 926), 1).save(os.path.join(R.VID, f"test_broll_{i}.png"))

im = R.make_ledger(1, 860, 1180)
im.convert("RGB").save(os.path.join(R.VID, "test_ledger.png"))
ex = R.make_excel(2, 980, 700)
ex[0].convert("RGB").save(os.path.join(R.VID, "test_excel.png"))
ex[1].convert("RGB").save(os.path.join(R.VID, "test_sticky.png"))
R.make_notebook(3, 400, 540, "报修记录本", (150, 60, 50)).convert("RGB").save(os.path.join(R.VID, "test_nb.png"))
print("ok")
