# -*- coding: utf-8 -*-
"""米游社扫码登录工具。

用米游社 App 扫一下就能拿到 Cookie，不用手动复制。

用法::

    python service/tools/qr_login.py
    python service/tools/qr_login.py --uid 114172341

如果没有安装二维码库，会打印一个链接，你可以用手机打开它扫码，
或者装一下让二维码直接显示：``pip install qrcode``
"""

from __future__ import annotations

import argparse
import os
import sys
import time

_SERVICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _SERVICE)

from hsr.api import mys, qrlogin  # noqa: E402
from hsr.store import db  # noqa: E402

SERVERS = {
    '1': ('prod_gf_cn', '国服'),
    '2': ('prod_official_asia', '国际服 Asia'),
    '3': ('prod_official_usa', '国际服 America'),
    '4': ('prod_official_eur', '国际服 Europe'),
    '5': ('prod_official_cht', '国际服 TW/HK/MO'),
}

STATUS_TEXT = {
    'Created': '等待扫码',
    'Scanned': '已扫码，请在手机上确认',
    'Confirmed': '已确认',
}


def _ask_server() -> str:
    print('\n选择服务器：')
    for k, (_, label) in SERVERS.items():
        print(f'  {k}. {label}')
    raw = input('输入序号（回车 = 1 国服）: ').strip() or '1'
    return SERVERS.get(raw, SERVERS['1'])[0]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='米游社扫码登录')
    ap.add_argument('--uid', help='游戏 UID（省略则用已登记的默认 UID）')
    ap.add_argument('--timeout', type=float, default=180, help='等待扫码秒数')
    ap.add_argument('--no-save', action='store_true', help='只登录不写入数据库')
    args = ap.parse_args(argv)

    print('=' * 60)
    print('星穹铁道 · 米游社扫码登录')
    print('=' * 60)
    print('用米游社 App 扫描二维码并确认即可，无需手动复制 Cookie。')
    print('Cookie 只会写入本机数据库。\n')

    # 1. 创建二维码
    try:
        qr = qrlogin.create_qr()
    except qrlogin.QRLoginError as e:
        print(f'❌ 创建二维码失败：{e}')
        return 1

    print(f'ticket: {qr.ticket}')
    png = None
    if qrlogin.qr_available():
        out_dir = os.path.join(db.DATA_DIR, 'media')
        os.makedirs(out_dir, exist_ok=True)
        png = qrlogin.render_qr_png(qr.url, os.path.join(out_dir, f'qr-{qr.ticket[:8]}.png'))
    if png:
        print(f'\n二维码图片: {png}')
        try:
            os.startfile(png)  # Windows
        except Exception:
            pass
    else:
        print('\n（未安装二维码库，无法本地生成图片）')
        print('  可以装一下：pip install qrcode')
        print('  或用手机打开这个链接所在页面扫码：')
    print(f'\n二维码内容:\n  {qr.url}\n')

    # 2. 轮询
    last = ''

    def on_status(st: qrlogin.QRStatus) -> None:
        text = STATUS_TEXT.get(st.status, st.status)
        print(f'  [{time.strftime("%H:%M:%S")}] {text}')

    print('等待扫码……')
    try:
        status = qrlogin.poll_status(qr.ticket, timeout=args.timeout, on_status=on_status)
    except qrlogin.QRLoginError as e:
        print(f'❌ {e}')
        return 1

    if not status.confirmed:
        print(f'❌ 扫码未完成，最终状态：{status.status}')
        return 1

    # 3. 构造 Cookie
    try:
        cookie = qrlogin.build_cookie(status)
    except qrlogin.QRLoginError as e:
        print(f'❌ {e}')
        return 1

    print(f'\n✅ 扫码成功，已获取 Cookie（{len(cookie)} 字节）')

    # 4. 确定 UID 并校验
    uid = args.uid or db.get_default_uid()
    if not uid:
        uid = input('游戏 UID（例如 114172341）: ').strip()
    if not uid.isdigit():
        print(f'❌ UID 不合法：{uid!r}')
        return 1

    server = _ask_server()

    print('\n正在校验 Cookie……')
    parsed = mys.parse_cookie(cookie)
    try:
        data = mys.check_cookie(uid, server, parsed)
    except mys.MysError as e:
        print(f'❌ 校验失败：{e}')
        print('   Cookie 已获取但无法查询，可能该账号没有这个角色，或服务器选错了。')
        return 1

    role = data.get('role') or {}
    nickname = role.get('nickname') or ''
    level = int(role.get('level') or 0)

    print(f'✅ 校验通过：{nickname}  Lv{level}')

    if args.no_save:
        print('\n(--no-save) 未写入数据库。Cookie 如下（请勿外传）：')
        print(f'  {cookie[:20]}…（已省略）')
        return 0

    db.save_account(uid, cookie, server=server, nickname=nickname, level=level)
    print(f'\n✅ 已保存到 {db.DB_PATH}')
    print('\n接下来可以试：')
    print('   python service/tools/query.py 查询')
    print('   python service/tools/query.py 混沌')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
