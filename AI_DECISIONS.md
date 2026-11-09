# 决策记录

记录本项目里需要取舍的地方，以及为什么这么选。

---

## 2026-11-09 出图：Playwright 还是 Pillow

**待定问题**：查询结果要出图，用浏览器渲染 HTML，还是直接用 Pillow 画像素？

**背景约束**：起初希望插件不引入第三方依赖（服务端只用标准库），
且本机当时并未安装 Python 版 Playwright（鸣潮插件一直在走「外置渲染」降级）。

**候选方案**

1. **Pillow 直接绘制**：手算坐标画矩形和文字。零浏览器依赖，冷启动毫秒级。
   代价是排版全靠手工，渐变/阴影/字重都很难做，改版式要改代码。
2. **Playwright 渲染 HTML**：写 CSS 出图。排版自由度高、接近游戏 UI。
   代价是首次要下载约 120MB 浏览器，单次渲染约 7 秒。
3. **自己写二维码/图形编码器**：试图完全不依赖。后来证明是不必要的投入。

**选择**：以 Playwright 为主路径，Pillow 作二级降级，纯文字兜底。

**选择理由**：用户明确允许引入依赖并安装了 Playwright 与浏览器。
HTML 出来的卡片在字体、间距、阴影、等宽数字上都明显更好，
而 7 秒的渲染延迟对查询类操作可以接受（结果另有缓存）。

**未选原因**

- Pillow 单用：作为唯一方案时版式上限太低；现在保留它专门处理
  「Playwright 不可用」和「画二维码」两种场景，性价比刚好。
- 自研编码器：二维码编码器写到一半已能对齐码字流，但矩阵排布仍有差异。
  用户放行依赖后，用 `qrcode` 库两行解决，继续手写是浪费。

**验证方式**：`tests/test_htmlcard.py` 里有一项会真的启动 chromium 截图并校验 PNG 头；
`/api/health` 会报告当前生效的渲染器（实测 `render: "playwright"`）。

**风险与回滚**：Playwright 起不来时自动降级到 Pillow，再不行退纯文字，
功能不会中断。彻底回滚只需删掉 `service/hsr/render/htmlcard.py` 并把
`CommandResult.render_png` 改为直接调 Pillow。

---

## 2026-11-09 扫码登录：走 web 端点还是 app 端点

**待定问题**：米游社扫码登录的接口该用哪个。官方 SDK 同时列了 web 与 app 两条路径。

**背景约束**：miao-plugin 自身没有扫码登录（它依赖 Yunzai 的 Cookie 绑定），
需要从零验证接口。

**候选方案**

1. **web 端点** `/account/ma-cn-passport/web/createQRLogin`：按直觉先试。
2. **app 端点** `/account/ma-cn-passport/app/createQRLogin`：社区实现用的路径。

**选择**：app 端点，域名用 `passport-api.mihoyo.com`。

**选择理由**：实测 web 端点在补了 `app_id`、`x-rpc-app_id`、请求体等所有组合后
一律返回 `-3001 参数不合法`；app 端点在带上
`x-rpc-app_id` / `x-rpc-client_type=3` / `x-rpc-app_version` 后直接 `retcode=0`，
拿到 ticket 与二维码 URL。这是唯一可用的组合。

**未选原因**：web 端点所有参数组合均失败，没有继续试的价值。

**验证方式**：真实调用拿到 ticket（`3fdc2fa7-…`），二维码渲染成功，
`queryQRLoginStatus` 返回 `status: "Created"`。单测覆盖 token→Cookie 映射与状态位。

**风险与回滚**：`x-rpc-app_version` 之类参数官方随时可能调整，
失效时返回 `-3001`。届时更新 `api/qrlogin.py` 顶部的常量即可；
扫码不可用不影响手动粘贴 Cookie 的老路径。

**未验证**：真实扫码确认后的 `tokens` 字段形状与 `token_type` 映射。
映射按社区常见实现写成 1=stoken / 2=ltoken / 3=cookie_token，需要扫一次才知道对不对。

---

## 2026-11-09 遗器评分：直接搬 miao-plugin 还是重写

**待定问题**：评分算法与权重表怎么处理。

**选择**：权重表与套装数值直接生成（`scripts/harvest_miao.py` 自动抓取），
评分算法移植成 Python 但保持与上游逐项对齐。

**选择理由**：权重表是 106 个角色的经验数据，重写没有意义；
算法移植时才能顺手修掉上游口径里的坑（雷属性字段、
头/手主词条不该建议更换、缺件按 6 件折算）。

**验证方式**：13 项单测覆盖评级边界、权重表抽样、缺件、
异色球、无效词条提示；再用真实账号跑一遍，评级排序与人工分析一致。

**风险与回滚**：上游改表时重跑 `harvest_miao.py` 即可；
算法层面若与上游产生分歧，以本仓库注释与测试为准。
