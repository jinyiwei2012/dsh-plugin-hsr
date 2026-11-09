# -*- coding: utf-8 -*-
"""扫码登录 · 后台监听版。

一次做完整个流程，不需要人工在两轮对话间来回：

1. 创建二维码并写出 PNG
2. 打印 PNG 路径（供上层取用展示）
3. 立刻开始轮询，直到确认或过期
4. 确认后构造 Cookie、校验、写入数据库

二维码有效期只有约 90 秒，所以「创建」和「轮询」必须紧挨着做，
不能等用户回话再查——那样八成已经 -3501 了。

用法::

    python service/tools/qr_watch.py --uid 114172341 --timeout 120
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

SERVERS = {'prod_gf_cn', 'prod_official_asia', 'prod_official_usa',
           'prod_official_eur', 'prod_official_cht'}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='扫码登录后台监听')
    ap.add_argument('--uid', help='游戏 UID')
    ap.add_argument('--server', default='prod_gf_cn', help='服务器')
    ap.add_argument('--timeout', type=float, default=120, help='最长等待秒数')
    ap.add_argument('--interval', type=float, default=2.0, help='轮询间隔')
    args = ap.parse_args(argv)

    uid = args.uid or db.get_default_uid()
    server = args.server if args.server in SERVERS else 'prod_gf_cn'

    # 1. 创建二维码
    try:
        qr = qrlogin.create_qr()
    except qrlogin.QRLoginError as e:
        print(f'CREATE_FAIL {e}')
        return 1

    out_dir = os.path.join(db.DATA_DIR, 'media')
    os.makedirs(out_dir, exist_ok=True)
    png = qrlogin.render_qr_png(qr.url, os.path.join(out_dir, f'qr-{qr.ticket[:8]}.png'))
    db.set_setting('login_ticket', qr.ticket)
    print(f'QR_PATH {png}', flush=True)
    print(f'TICKET {qr.ticket}', flush=True)
    print(f'UID {uid}  SERVER {server}', flush=True)

    # 2. 立刻轮询（有效期只有 ~90 秒）
    deadline = time.time() + args.timeout
    last = ''
    while time.time() < deadline:
        try:
            st = qrlogin.query_status(qr.ticket)
        except qrlogin.QRLoginError as e:
            print(f'POLL_ERROR {e}', flush=True)
            return 1

        if st.status != last:
            last = st.status
            print(f'STATUS {st.status}', flush=True)

        if st.expired:
            print('EXPIRED', flush=True)
            return 2

        if st.confirmed:
            print(f'CONFIRMED tokens={len(st.tokens)} user_info={st.user_info}', flush=True)
            for t in st.tokens:
                tok = str(t.get('token') or '')
                print(f'  TOKEN type={t.get("token_type")} len={len(tok)}', flush=True)

            try:
                cookie = qrlogin.build_cookie(st)
            except qrlogin.QRLoginError as e:
                print(f'BUILD_FAIL {e}', flush=True)
                return 1

            # 先落盘：校验失败也不用重新扫码，可以离线改请求头重试
            db.set_setting('pending_cookie', cookie)
            db.set_setting('pending_cookie_uid', uid)
            db.set_setting('pending_cookie_server', server)
            print(f'COOKIE_BUILT len={len(cookie)}', flush=True)
            fields = [p.split('=')[0] for p in cookie.split(';')]
            print(f'COOKIE_FIELDS {fields}', flush=True)

            parsed = mys.parse_cookie(cookie)
            try:
                ctype, ver, data = mys.probe_headers(uid, server, parsed)
            except mys.MysError as e:
                # 10041 = 鉴权通过但战绩未公开。凭据本身是好的，
                # 必须入库，否则用户去打开隐私设置后还得重扫一次。
                if e.retcode == 10041 or '10041' in str(e):
                    db.save_account(uid, cookie, server=server,
                                    nickname='', level=0)
                    db.set_setting('pending_cookie', '')
                    db.set_setting('mys_client_type', '5')
                    db.set_setting('mys_app_version', '2.11.1')
                    print('CREDENTIAL_OK 凭据有效（10041 只是战绩未公开）', flush=True)
                    print(f'SAVED UID {uid}（待打开隐私设置后即可查全部角色与战绩）',
                          flush=True)
                    return 0
                print(f'VERIFY_FAIL {e}', flush=True)
                print('COOKIE_KEPT 已保存到 settings.pending_cookie，可离线重试', flush=True)
                return 1

            role = data.get('role') or {}
            nickname = role.get('nickname') or ''
            level = int(role.get('level') or 0)
            db.save_account(uid, cookie, server=server, nickname=nickname, level=level)
            db.set_setting('login_ticket', '')
            db.set_setting('pending_cookie', '')
            db.set_setting('mys_client_type', ctype)
            db.set_setting('mys_app_version', ver)
            print(f'HEADER_OK client_type={ctype!r} app_version={ver!r}', flush=True)
            print(f'SAVED UID {uid}  {nickname}  Lv{level}', flush=True)
            return 0

        time.sleep(args.interval)

    print('TIMEOUT', flush=True)
    return 3


if __name__ == '__main__':
    raise SystemExit(main())
