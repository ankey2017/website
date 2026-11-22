# -*- coding: utf-8 -*-
"""资管易 · 小红书专版：不含官网与电话，收尾改为评论区互动"""
from project_asset import *  # noqa

SLUG = "assetxhs"
POSTER_MODE = "xhs"
OFFICIAL = ""          # 小红书店不放站外链接
SLOGAN = "一套台账管到底，家底管得明白"
SUB_SLOGAN = "林子软件 · 中小企业经营管理工具"

# 第四段口播改为互动引导，不再提「访问官网」
TEXT = dict(TEXT)
TEXT["s4"] = "想看看这套台账是怎么搭起来的，评论区聊。"
