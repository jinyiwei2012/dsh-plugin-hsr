# -*- coding: utf-8 -*-
"""用 stoken 直接派生 Cookie 并验证战绩接口（不依赖扫码）。

用途：验证「stoken 派生 → 战绩可读」这条链路是否成立。
如果成立，扫码登录后拿到的 stoken 就能直接出数据，不用再猜头。

用法::

    python scripts/probe_stoken.py --stoken <STOKEN> [--uid 114172341]

也可以把 stoken 放进环境变量 ``HSR_MYS_STOKEN``，避免出现在命令行历史里。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'service'))

from hsr.api import mys, qrlogin  # noqa: E402

PASSPORT = 'https://passport-api.mihoyo.com'
URL_LTOKEN = '/account/auth/api/getLTokenBySToken'
URL_ACCOUNT = '/account/auth/api/getCookieAccountInfoBySToken'
URL_BINDING = ('https://api-takumi.mihoyo.com/binding/api/getUserGameRolesByCookie'
               '?game_biz=hkrpg_cn')


def raw_get(url: str, cookie: str) -> tuple[int | None, str]:
    headers = {
        'User-Agent': qrlogin.APP_UA,
        'Accept': 'application/json',
        'Cookie': cookie,
        'x-rpc-app_id': qrlogin.APP_ID,
        'x-rpc-client_type': '3',
        'x-rpc-app_version': qrlogin.APP_VERSION,
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'ignore')[:160]
    except Exception as e:  # noqa: BLE001
        return None, f'{type(e).__name__}: {e}'
    try:
        d = json.loads(body)
    except Exception:  # noqa: BLE001
        return None, body[:160]
    return d.get('retcode'), json.dumps(d.get('data'), ensure_ascii=False)[:220]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--stoken', default=os.environ.get('HSR_MYS_STOKEN') or '')
    ap.add_argument('--uid', default='114172341')
    ap.add_argument('--server', default='prod_gf_cn')
    args = ap.parse_args()

    if not args.stoken:
        print('缺少 stoken')
        return 2

    st = args.stoken

    print('--- 1. 用 stoken 换凭据 ---')
    mid = ''
    rc, data = raw_get(PASSPORT + URL_ACCOUNT, f'stoken={st}')
    print(f'  getCookieAccountInfoBySToken  retcode={rc} {data}')
    try:
        parsed = json.loads(data) if data.startswith('{') else {}
        mid = str(parsed.get('mid') or '')
    except Exception:  # noqa: BLE001
        pass
    time.sleep(1.4)

    ltoken = ''
    rc, data = raw_get(PASSPORT + URL_LTOKEN, f'stoken={st}')
    print(f'  getLTokenBySToken             retcode={rc} {data}')
    time.sleep(1.4)

    print()
    print('--- 2. 用 stoken 查绑定角色 ---')
    rc, data = raw_get(URL_BINDING, f'stoken={st}; mid={mid}')
    print(f'  retcode={rc} {data}')
    time.sleep(1.4)

    print()
    print('--- 3. 用 stoken 直接打崩铁 index（不派生 ltoken）---')
    cookie = mys.parse_cookie(f'stoken={st}')
    try:
        data = mys.fetch_index(args.uid, args.server, cookie)
        print('  OK 字段:', ', '.join(list(data)[:8]))
    except mys.MysError as e:
        print(f'  {e}')
    time.sleep(1.4)

    print()
    print('--- 4. 走 build_cookie（stoken → ltoken → Cookie）---')
    try:
        ck = qrlogin.build_cookie(
            qrlogin.QRStatus(status='Confirmed',
                             tokens=[{'token_type': 1, 'token': st}],
                             user_info={'mid': mid} if mid else {}))
        print('  Cookie 字段:', sorted(mys.parse_cookie(ck).__dict__))
        data = mys.fetch_index(args.uid, args.server, mys.parse_cookie(ck))
        role = data.get('role') or {}
        print(f'  OK nickname={role.get("nickname")} level={role.get("level")}')
    except (mys.MysError, qrlogin.QRLoginError) as e:
        print(f'  {e}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
