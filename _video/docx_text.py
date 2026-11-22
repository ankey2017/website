# -*- coding: utf-8 -*-
"""从 docx 提取纯文本（不依赖 python-docx）"""
import sys, zipfile, re, os

src = sys.argv[1]
out = sys.argv[2]
with zipfile.ZipFile(src) as z:
    xml = z.read("word/document.xml").decode("utf-8", "ignore")

# 段落切分
paras = re.split(r"</w:p>", xml)
lines = []
for p in paras:
    # 提取所有 w:t 文本
    texts = re.findall(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", p, re.S)
    t = "".join(texts)
    t = (t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
          .replace("&quot;", '"').replace("&apos;", "'"))
    t = t.strip()
    if t:
        lines.append(t)
open(out, "w", encoding="utf-8").write("\n".join(lines))
print("paras", len(lines))
