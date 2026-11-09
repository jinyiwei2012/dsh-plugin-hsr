# -*- coding: utf-8 -*-
"""用已保存的 pending_cookie 离线排查 10041。

试两个维度：
  1. server 取值（可能选错服务器）
  2. Cookie 字段组合（v1 / v2 命名）
"""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = r'C:\Users\Administrator\dsh-plugins\dsh-plugin-hsr'
sys.path.insert(0, ROOT + r'\service')

from hsr.api import mys  # noqa: E402
from hsr.store import db  # noqa: E402

OUT = ROOT + r'\scripts\_probe_10041.txt'
L = []


def w(s=''):
    L.append(str(s))
    print(s, flush=True)


cookie_raw = db.get_setting('pending_cookie')
uid = db.get_setting('pending_cookie_uid') or db.get_default_uid()
if not cookie_raw:
    w('没有 pending_cookie')
    raise SystemExit(1)

w(f'pending_cookie 长度 {len(cookie_raw)}')
byname = {}
for part in cookie_raw.split(';'):
    part = part.strip()
    if '=' in part:
        k, _, v = part.partition('=')
        byname[k.strip()] = v.strip()
w(f'字段: {list(byname)}')
w(f'ltuid = {byname.get("ltuid", "")[:8]}...')
w(f'ltoken = {byname.get("ltoken", "")[:12]}...')
w(f'cookie_token = {byname.get("cookie_token", "")[:12]}...')
w(f'stoken 长度 {len(byname.get("stoken", ""))}')
w(f'UID {uid}')
w('')


def call(server: str, cookie: str, path: str = mys.PATH_INDEX) -> str:
    """直接用 web/2.11.1 那组头（唯一签名能过的）发一次请求。"""
    params = {'role_id': str(uid), 'server': server}
    query = urllib.parse.urlencode(sorted(params.items()))
    ds = mys.make_ds(query)
    url = f'{mys.HOST}{path}?{query}'
    headers = {
        'User-Agent': mys.UA,
        'Accept': 'application/json',
        'Cookie': cookie,
        'DS': ds,
        'x-rpc-app_version': '2.11.1',
        'x-rpc-client_type': '5',
        'x-rpc-language': 'zh-cn',
        'Referer': 'https://app.mihoyo.com/',
        'Origin': 'https://app.mihoyo.com',
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            body = r.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        return f'HTTP {e.code}'
    except Exception as e:
        return f'{type(e).__name__}: {e}'
    try:
        d = json.loads(body)
    except json.JSONDecodeError:
        return f'非 JSON: {body[:120]}'
    rc = d.get('retcode')
    msg = d.get('message')
    if rc == 0:
        data = d.get('data') or {}
        role = data.get('role') or {}
        return f'OK nickname={role.get("nickname")} level={role.get("level")}'
    return f'{rc} {msg}'


# ---------- 1. 换服务器 ----------
w('=== 按服务器试 ===')
SERVERS = ['prod_gf_cn', 'prod_official_asia', 'prod_official_usa',
           'prod_official_eur', 'prod_official_cht']
for sv in SERVERS:
    r = call(sv, cookie_raw)
    w(f'  {sv:22s} {r}')
    time.sleep(1.2)

# ---------- 2. 换 Cookie 字段命名 ----------
w('')
w('=== 按 Cookie 字段组合试（服务器用 prod_gf_cn）===')
ltuid = byname.get('ltuid', '')
ltoken = byname.get('ltoken', '')
ct = byname.get('cookie_token', '')
st = byname.get('stoken', '')
mid = byname.get('mid', '')

variants = {
    'ltuid+ltoken': f'ltuid={ltuid}; ltoken={ltoken}',
    'ltuid+ltoken+cookie_token': f'ltuid={ltuid}; ltoken={ltoken}; cookie_token={ct}',
    'ltuid_v2+ltoken_v2': f'ltuid_v2={ltuid}; ltoken_v2={ltoken}',
    'ltmid_v2+ltoken_v2': f'ltmid_v2={ltuid}; ltoken_v2={ltoken}',
    'account_id+ltoken': f'account_id={ltuid}; ltoken={ltoken}',
    'stuid+ltoken': f'stuid={ltuid}; ltoken={ltoken}',
    '全量(原始)': cookie_raw,
    'cookie_token_v2': f'ltuid={ltuid}; cookie_token_v2={ct}',
}
for name, ck in variants.items():
    r = call('prod_gf_cn', ck)
    w(f'  {name:26s} {r}')
    time.sleep(1.2)

# ---------- 3. 无 Cookie 对照 ----------
w('')
w('=== 对照：完全不发 Cookie ===')
w(f'  no-cookie                  {call("prod_gf_cn", "")}')

open(OUT, 'w', encoding='utf-8').write('\n'.join(L))
print()
print('written', OUT)
