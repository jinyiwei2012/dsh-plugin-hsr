# 决策记录

记录本项目里需要取舍的地方，以及为什么这么选。

---

## 2026-11-09 评分卡：自己设计版式还是复刻 miao

**待定问题**：遗器评分卡长什么样。

**背景约束**：初版用通用区块渲染，每件遗器一条通栏列表。实际渲染出来
整张图 660×1397，每件遗器占满整行，视觉上很松散。

**调研参考**：直接读了 miao-plugin 的模板与样式
（`resources/character/artis-mark.{html,css}`、`profile-detail.css`），
拿到真实数值。

**关键发现**：miao 的遗器**不是通栏列表**，而是 ``.artis`` flex 网格里
每件 185px 宽的小卡，每行 3 张；角色信息绝对定位在**右上角**、右对齐；
立绘 ``1400×520`` 且 ``background-size: contain``，靠 ``margin-left:-545px``
居中后被 660 宽窗口横向裁切；遗器网格再用 ``margin-top:-280px`` 压到立绘下半部。

**选择**：按上游数值 1:1 复刻。

**选择理由**：用户明确要求「1:1 复刻」。而且上游这套数值是长期调过的，
紧凑度与信息密度比我自己临时设计的更合理。

**未选原因**

- 通用区块版式：每件占一行，卡片过高，信息密度低，与上游观感差距大。
- 完全照抄 CSS 布局机制：上游用 ``display:table/table-row`` 排词条行，
  在 flex 子项里会高度塌陷（实测卡片互相叠在一起）。改用等价的 flex 行，
  行高、列宽、配色仍与上游一致，只是布局机制不同。

**踩到的坑**：`.detail`（角色信息块）是 `position:absolute`，
遗器里的 `ul.detail` 若不显式 `position:static`，会被一起拽成绝对定位，
导致六张卡片全部重叠。上游模板里写了 `position:initial`，第一版移植时漏了。

**验证方式**：`tests/test_artiscard.py` 13 项，覆盖版式结构（立绘、
图标 URL、评级配色、无效词条类名、固定主词条显示 `-`）与真实截图；
实拍图见 `docs/screenshot-arti.png`。

**风险与回滚**：立绘与遗器图标来自社区资源库
Mar-7th/StarRailRes（jsDelivr 分发），断网时图片空白但版式不塌。
上游若改版式，重跑提取脚本对齐即可；本文件顶部记录了取值来源。

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

---

## 2026-11-09 战绩接口 10041：是「签名问题」还是「账号状态」

**待定问题**：米游社战绩接口（`api-takumi-record.mihoyo.com`）对本账号的崩铁角色
一直返回 `retcode=10041`（`message` 为空）。此前把原因挂在了签名上，
但这会走错方向，需要先定位清楚再改代码。

**背景约束**：扫码登录已能拿到 stoken，也能换出 ltoken，但换成可用 Cookie 后
`index` / `avatar/info` / `challenge` 三个接口全部是 10041。

**排查过程与证据**（均为本机实测，同一份网页 Cookie）：

1. **账号与角色是匹配的**。`getUserGameRolesByCookie?game_biz=hkrpg_cn`
   返回 `retcode=0`，列表里有 `114172341 / prod_gf_cn / 洛天依 / Lv70`。
   → 「Cookie 和 UID 不是同一个号」这个假设被推翻。
2. **签名是被接受的**。同一份 Cookie、同一套签名打**原神** `index`，
   返回业务层的 `5003`，而不是 `-10001 invalid request`。
   → salt 与 `x-rpc-app_version` 组合正确，DS 算法没问题。
3. **不是 header 组合问题**。穷举 10 个 `app_version`（2.11.1 → 3.0.0），
   崩铁全部 10041、原神全部 5003；再叠加 `x-rpc-device_id` / `device_fp` /
   `device_name` / `sys_version` / `channel` / App UA / `X-Requested-With`
   一共 7 组附加头，崩铁依然全是 10041。
4. **不是签名算法版本问题**。DS1（`r` 取 6 位字母数字）与
   DS2（`r` 取 100000..200000 整数，[UIGF 文档](https://uigf.org/zh/mihoyo-api-collection/other/authentication.html)
   给的标准写法）两种写法都是 10041。
5. **cookie 字段组合矩阵**：
   `ltmid_v2 + ltoken_v2` → **10041**；
   其余所有组合（无 cookie、只 ltoken_v2、ltuid_v2+ltoken_v2、
   cookie_token_v2、ltuid_v2+cookie_token_v2、三者齐全）→ `10001 Please login`。
   → 说明 `ltmid_v2 + ltoken_v2` 是**被接受的凭据组合**，鉴权确实过了，
   10041 是在鉴权之后的业务层返回。
6. **最关键的定位实验**——同一份 Cookie 下换 `role_id`：

   | `role_id` | 返回 | 含义 |
   |---|---|---|
   | `114172341`（本账号） | `10041` | 命中了某项账号级限制 |
   | `999999999`（不存在） | `1008 用户信息不匹配` | 不是鉴权墙，是先做 UID 校验 |
   | `100000001`（别人的号） | `10102 Data is not public for the user` | 同上，进入了业务层 |
   | 任意 UID（无 Cookie） | `10001 Please login` | 未登录 |

   如果 10041 是「这道墙你过不去」，那**所有** UID 都该是 10041 或 10001。
   实际是「只有本账号的号报 10041，别人的号能走进业务层」——
   所以 10041 是**本账号在米游社侧的状态**，不是接口拒绝我们的请求。
7. **`server` 参数校验正常**：`prod_gf_cn` → 10041；
   `prod_official_asia` / `cn_gf01` / `bogus` → `-1 param error`。
   说明参数被正常解析，没有卡在参数层。

**结论**：`10041` 等价于「该角色的战绩数据未公开 / 被隐藏」。
玩家可以在**米游社 App → 我的 → 游戏角色 → 角色卡片 → 隐私设置**里
把「公开我的角色详情」打开。关掉打码后，同一套代码不需要任何修改就能读到数据——
这一点是本轮**未能验证**的（改动需要账号持有人操作），
必须标注为待验证，不能当作已经修好。

**采纳的策略**（代码层面）：

1. **mihomo 公开接口作为免登录主路径**（`api.mihomo.me/sr_info_parsed/<uid>`）。
   它只给展柜里的角色，但**不需要任何凭据**，也不受打码影响，现在就能用。
2. **扫码登录作为完整路径**（`getUserGameRolesByCookie` 走 stoken → 派生 Cookie），
   在打码打开后自动生效，用来拿全部角色与战绩。
3. **网页 Cookie 不再作为战绩来源**，只用于「查账号绑定了哪些角色」这类
   不需要角色详情的只读操作。
4. 报错信息要把 `10041` 翻译成可操作的中文提示（去米游社关打码），
   而不是把 retcode 丢给用户。

**验证方式**：`scripts/probe_10041.py` 可离线复现第 5、7 两项矩阵；
Cookie 说明见 `docs/cookie.md`。打码关闭后的真实读数待用户操作后补验。

**顺手修掉的一个真 bug**：`qr_watch.py` 之前只要 `probe_headers` 抛异常就
`return 1`，凭据停留在 `settings.pending_cookie` 而不入库。
但 10041 属于「凭据有效、只是数据没公开」，这种情况也应该入库——
否则用户去打开隐私设置之后还得**重新扫一次码**。
现在遇到 10041 会正常 `save_account`，只是昵称/等级暂时为空，改完设置直接查即可。

**风险与回滚**：mihomo 只需要 UID，无凭据风险；扫码登录产生的 Cookie 只落在
`service/data/hsr.db`（已 gitignore），不进仓库、不进日志。
回滚只需停用 Mys 数据源，mihomo 路径不受影响。

**附带清理**：本轮排查用的 5 个探针脚本把真凭据硬编码在源码里
（`probe_v2.py` / `probe_roles.py` / `probe_ds2.py` / `probe_headers2.py` /
`probe_versions.py`），虽然未推送，但仓库是公开的，已全部删除。
后续探针一律从 `db.get_setting()` 读凭据，不写死在文件里。
