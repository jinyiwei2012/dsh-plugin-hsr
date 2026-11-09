# 绑定米游社账号

绑定后能查到**账号下全部角色**（等级、星魂、光锥、遗器主副词条）以及战绩。
不绑定只能看游戏内「展柜」里展示的那几个角色。

---

## 方式一：扫码登录（推荐）

不用手动复制任何东西。

在对话里发：

```
你：登录
  → 插件出一张二维码
你：（用米游社 App 扫码并在手机上确认）
你：登录状态
  → 登录成功，UID 114172341  洛天依 Lv70
```

命令行版：

```bash
python service/tools/qr_login.py
```

流程是：创建 ticket → 出二维码 → 轮询状态（Created / Scanned / Confirmed）
→ 确认后取到 token → 拼成 Cookie → 校验 → 写入本机数据库。

> 需要 `qrcode` 与 `Pillow` 才能出二维码：
> `python -m pip install -r service/requirements.txt`

---

## 方式二：手动粘贴 Cookie

> Cookie 等同于登录凭据。本工具只把它写到本机
> `service/data/hsr.db`，不上传、不写日志、不进 git。
> 想撤销时直接删除该文件，或运行 `bind_cookie.py --delete <UID>`。

### 1. 用浏览器登录米游社

打开 <https://www.miyoushe.com/sr/> 并登录你的米哈游账号。

### 2. 打开开发者工具

按 `F12`（或 `Ctrl+Shift+I`），切到 **Network（网络）** 标签页。

### 3. 触发一次接口请求

在页面里随便点一个需要登录的板块，例如「战绩」或「我的角色」。
Network 列表里会出现发往 `api-takumi-record.mihoyo.com` 的请求。

### 4. 复制 Cookie

点开其中任意一条请求 → **Headers（标头）** → 找到 **Request Headers**
里的 `Cookie:`，把**整行值**复制下来（不含 `Cookie:` 这几个字也行）。

里面至少要包含这两项：

- `ltoken=...`
- `ltuid=...`

新版米游社可能叫 `ltoken_v2`（对应 ltoken）和 `ltuid_v2`（对应 ltuid），
两种命名工具都能识别。

> 也可以直接从浏览器 `设置 → 隐私 → Cookie` 里搜 `miyoushe.com` 找，
> 但用上面的方法更省事。

### 5. 运行绑定工具

```bash
python service/tools/bind_cookie.py
```

按提示输入：

1. 游戏 UID（9 位数字，例如 `114172341`）
2. 服务器（国服选 1）
3. 粘贴 Cookie（**输入内容不会回显**）

工具会立刻校验一次，成功会显示昵称与等级。

---

## 常见问题

**提示「登录态无效」**

Cookie 过期了。米游社的 `ltoken` 大约一个月失效一次，重新抓一次即可。

**提示「Cookie 缺少 ltoken / ltuid」**

复制不完整。回去确认整行 Cookie 都复制到了，特别是末尾的部分。

**提示「invalid request」（retcode -10001）**

签名可能过期了 —— 官方偶发更换 salt。
可以设置环境变量覆盖后重试：

```bash
set HSR_MYS_SALT=<新的salt>
```

**提示 UID 与服务器不匹配**

国服 UID 一般是 1 或 2 开头，国际服不同。确认选对了服务器。

---

## 风控

这是非官方接口，请求过快会被限流。插件内置了：

- 最小请求间隔 1.2 秒
- 失败指数退避重试
- 面板结果缓存 10 分钟

正常查询频率完全够用。请勿用于批量刷号。
