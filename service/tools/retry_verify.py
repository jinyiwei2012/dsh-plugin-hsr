# -*- coding: utf-8 -*-
"""用已保存的 pending_cookie 离线重试校验（不需要重新扫码）。

扫码时若校验失败，Cookie 已存进 settings.pending_cookie。
改完请求头/参数后直接跑这个脚本即可验证，不用再麻烦用户扫一次。

用法::

    python service/tools/retry_verify.py
"""

from __future__ import annotations

import os
import sys

_SERVICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _SERVICE)

from hsr.api import mys  # noqa: E402
from hsr.store import db  # noqa: E402


def main() -> int:
    cookie = db.get_setting('pending_cookie')
    if not cookie:
        print('没有待验证的 Cookie（settings.pending_cookie 为空）')
        return 1

    uid = db.get_setting('pending_cookie_uid') or db.get_default_uid()
    server = db.get_setting('pending_cookie_server') or 'prod_gf_cn'

    parsed = mys.parse_cookie(cookie)
    print(f'Cookie 长度 {len(cookie)}')
    print(f'  ltuid   = {parsed.ltuid[:6]}...' if parsed.ltuid else '  ltuid   = (空)')
    print(f'  ltoken  = {parsed.ltoken[:10]}...' if parsed.ltoken else '  ltoken  = (空)')
    ct = parsed.cookie_token
    print(f'  cookie_token = {ct[:10]}...' if ct else '  cookie_token = (空)')
    print(f'  usable  = {parsed.usable}')
    print(f'UID {uid}  SERVER {server}')
    print()

    print('逐个尝试请求头组合：')
    for label, ctype, ver in mys.HEADER_VARIANTS:
        try:
            data = mys._request(
                mys.PATH_INDEX, {'role_id': str(uid), 'server': server},
                parsed, client_type=ctype, app_version=ver)
        except mys.MysError as e:
            print(f'  ❌ {label:14s} {e}')
            continue
        role = data.get('role') or {}
        print(f'  ✅ {label:14s} 通了！ nickname={role.get("nickname")} '
              f'level={role.get("level")}')

        # 落库
        db.save_account(uid, cookie, server=server,
                        nickname=role.get('nickname') or '',
                        level=int(role.get('level') or 0))
        db.set_setting('pending_cookie', '')
        db.set_setting('mys_client_type', ctype)
        db.set_setting('mys_app_version', ver)
        print()
        print(f'已保存。建议把 client_type={ctype!r} app_version={ver!r} 固化到 mys.py')
        return 0

    print()
    print('所有组合都失败。可能原因：')
    print('  1. 该账号下没有这个 UID 的角色（服务器选错）')
    print('  2. Cookie 缺少 cookie_token 等必要字段')
    print('  3. 触发了官方风控（10041 常见于频繁请求）')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
