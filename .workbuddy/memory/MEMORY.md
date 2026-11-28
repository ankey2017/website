# 项目长期约定 — webHome（林子软件官网）

## 站点结构
- 静态站，纯 HTML + 内联 CSS/JS，无构建流程。根目录 `index.html`、`about.html`（售后与授权说明）、`about-us.html`（关于我们），产品页在 `products/<产品名>/index.html`。
- 图片资源统一放 `assets/img/<产品名>/`。

## 产品排序约定（重要）
- **新产品一律排最前**（用户 2026-11-28 明确要求）。首页 `product-grid` 的卡片顺序与全站导航中的产品顺序保持一致，均按「新 → 旧」。
- 当前顺序（11 款）：飞租通 droneRent → 播销通 liveSell → 物管通 estatePilot → 资管易 assetKeeper → 客销管家 autoCRM → 广告工程管家 adProManager → 仓管通 stockKeeper → 码小匠 codeCraft → 租管通 rentKeeper → 货物销售管理系统 saleSystem → 企档通 qidantong。
- 新增产品时：① 建 `products/<slug>/index.html`；② 在 `index.html` 的 `product-grid` **最前面**插入 pcard，并把后续卡片注释序号 +1；③ 用统一脚本重建所有页面 `<nav>`（产品页前缀 `../`，about.html 前缀 `products/`）。
- 首页 `pick-grid`（怎么选）同样把新产品放在最前。

## 硬性口径
- **购买渠道：只用爱发电**（商品链接 `https://ifdian.net/item/...`，主页 `https://ifdian.net/a/lin1030`）。禁止出现「极速卖码」等第三方发卡平台表述。
- **联系方式：18929748802**（林子，微信同号）。新增页面如需电话，必须与之一致；JSON-LD 内为 `+86-18929748802`。
- 授权模式统一表述为「买断制、一机一码、本地离线校验、1 次免费换机补发」。
- 未激活状态的表述差异：飞租通/播销通/客销管家/物管通只能「查看界面」，资管易可试录 10 项，其余为「试用版限额」。按钮文案随之区分「下载 Windows 版」与「下载 Windows 试用版」。

## 注意
- 产品页购买按钮若仍是 `【替换成...】` 占位，说明该商品链接未填写，属待补项。
- 全站通用模块：每个产品页「适合哪些人用」区块内的蓝色提示框（定制开发 + 网络版已上线提醒）、`about.html#custom` 定制节、结尾 CTA 追加「支持定制修改开发」。

## 宣传视频
- 已有脚本化出片流程：`_video/build_audio.py`（TTS+混音→timeline.json）→ `_video/vrender.py`（PIL 逐帧→ffmpeg）。
- 配置驱动：每个产品一个 `_video/project_<slug>.py`，用环境变量 `VP` 选择，产物为 `promo_<slug>.mp4` + `关键帧_<slug>/`。已有 estate / crm / ad / asset / assetxhs / livesell / stock / code，另有 `_video/vrender_story.py` 走小红书经验分享风（adstory）。
- 功能段屏数不固定：`vrender.py` 已改成读 `len(SCREENS)`，要几屏给几屏（截图少的产品就给 5~7 屏）。
- BGM 预设见 `build_audio.py` 的 `BGM_PRESETS`：a=90BPM 明快、b=78BPM 暖、c=102BPM 轻快、d=86BPM 朴实、e=96BPM 轻巧；项目里写 `BGM="e"` 切换。
- 改片长/改分镜只改项目配置或 `timeline`，无需重做画面；成片统一 9:16 / 30fps / H.264 / 60~62s。
- 出片前用 `_video/check_proj.py`、`widths_proj.py` 自检；edge-tts 需绕过沙箱代理（`dangerouslyDisableSandbox`）才能连通。
- 发小红书要用 `POSTER_MODE="xhs"` 的专版（片尾去掉官网/电话，换评论区引导），参考 `project_assetxhs.py`。

