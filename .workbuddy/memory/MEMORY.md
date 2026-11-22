# 项目长期约定 — webHome（林子软件官网）

## 站点结构
- 静态站，纯 HTML + 内联 CSS/JS，无构建流程。根目录 `index.html`、`about.html`（售后与授权说明）、`about-us.html`（关于我们），产品页在 `products/<产品名>/index.html`。
- 图片资源统一放 `assets/img/<产品名>/`。

## 硬性口径
- **购买渠道：只用爱发电**（商品链接 `https://ifdian.net/item/...`，主页 `https://ifdian.net/a/lin1030`）。禁止出现「极速卖码」等第三方发卡平台表述。
- **联系方式：18929748802**（林子，微信同号）。新增页面如需电话，必须与之一致；JSON-LD 内为 `+86-18929748802`。
- 授权模式统一表述为「买断制、一机一码、本地离线校验、1 次免费换机补发」。

## 注意
- 产品页购买按钮若仍是 `【替换成...】` 占位，说明该商品链接未填写，属待补项。

## 宣传视频
- 已有脚本化出片流程：`_video/build_audio.py`（TTS+混音→timeline.json）→ `_video/vrender.py`（PIL 逐帧→ffmpeg）。
- 配置驱动：每个产品一个 `_video/project_<slug>.py`（estate / crm / ad），用环境变量 `VP` 选择，产物为 `promo_<slug>.mp4` + `关键帧_<slug>/`。
- 改片长/改分镜只改项目配置或 `timeline`，无需重做画面；成片统一 9:16 / 30fps / H.264 / 60~62s。
- 出片前用 `_video/check_proj.py`、`widths_proj.py` 自检；edge-tts 需绕过沙箱代理（`dangerouslyDisableSandbox`）才能连通。

