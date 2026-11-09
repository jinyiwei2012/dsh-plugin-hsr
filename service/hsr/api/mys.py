# -*- coding: utf-8 -*-
"""米游社（miHoYo BBS）星穹铁道战绩接口客户端。

登录态来自浏览器 Cookie（ltuid + ltoken），可以拿到**全部角色**与战绩，
比 mihomo 公开接口（只有展柜）完整得多。

签名
----
接口要求 ``DS`` 头::

    t = unix 秒级时间戳
    r = 6 位随机串
    h = md5(f"salt={SALT}&t={t}&r={r}&b={body}&q={query}")
    DS = f"{t},{r},{h}"

国服 salt 为 ``xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs``。该值由官方前端下发，
官方调整后需要同步更新（可通过 ``HSR_MYS_SALT`` 环境变量覆盖）。

风险提示
--------
这是非官方接口。请求过快会被风控（返回 -100 / 需要验证码），因此本模块
内置了最小请求间隔与失败重试退避。请勿高频调用。
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import string
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

HOST = 'https://api-takumi-record.mihoyo.com'
PATH_INDEX = '/game_record/app/hkrpg/api/index'
PATH_AVATAR = '/game_record/app/hkrpg/api/avatar/info'
PATH_CHALLENGE = '/game_record/app/hkrpg/api/challenge'

SALT_CN = os.environ.get('HSR_MYS_SALT') or 'xV8v4Qu54lUKrEYFZkJhB8cuOh9Asafs'
APP_VERSION = os.environ.get('HSR_MYS_APP_VERSION') or '2.11.1'

UA = ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

# 最小请求间隔（秒），避免触发风控
MIN_INTERVAL = 1.2
# 失败重试次数
MAX_RETRY = 2
TIMEOUT = 25

_lock = threading.Lock()
_last_call = 0.0


class MysError(RuntimeError):
    """米游社接口错误。"""

    def __init__(self, message: str, retcode: int | None = None):
        super().__init__(message)
        self.retcode = retcode


# 10041 的实测定位结论（见 AI_DECISIONS.md）：
#   同一份 Cookie 下，本账号的 role_id → 10041；
#   不存在的 role_id → 1008；别人的 role_id → 10102；无 Cookie → 10001。
#   说明 10041 不是鉴权失败，而是「该角色的战绩没公开」。
RETCODE_10041_HINT = (
    '该角色的战绩数据未公开（retcode 10041）。\n'
    '这不是插件的问题，也不是 Cookie 失效——米游社侧把这个号的详情隐藏了。\n'
    '打开方式：米游社 App → 我的 → 我的角色 → 点进崩铁角色卡片 → 隐私设置\n'
    '        → 打开「公开我的角色详情」与「显示我的战绩」。\n'
    '改完后重新查询即可，无需重新绑定。\n'
    '在此期间仍可用免登录的展柜数据（仅展柜内角色）。'
)


@dataclass
class ParsedCookie:
    """从浏览器 Cookie 里解析出的登录凭据。"""

    raw: str
    ltuid: str = ''
    ltoken: str = ''
    cookie_token: str = ''
    account_id: str = ''

    @property
    def usable(self) -> bool:
        return bool(self.ltoken and (self.ltuid or self.account_id))


def parse_cookie(cookie: str) -> ParsedCookie:
    """解析浏览器复制来的 Cookie 串。"""
    raw = (cookie or '').strip()
    # 允许直接把整行 "Cookie: xxx" 贴进来
    if raw.lower().startswith('cookie:'):
        raw = raw[7:].strip()

    jar: dict[str, str] = {}
    for part in raw.split(';'):
        part = part.strip()
        if not part or '=' not in part:
            continue
        k, _, v = part.partition('=')
        jar[k.strip()] = v.strip()

    def pick(*names: str) -> str:
        for n in names:
            if jar.get(n):
                return jar[n]
        return ''

    return ParsedCookie(
        raw=raw,
        ltuid=pick('ltuid_v2', 'ltuid', 'account_id_v2', 'account_id'),
        ltoken=pick('ltoken_v2', 'ltoken'),
        cookie_token=pick('cookie_token_v2', 'cookie_token'),
        account_id=pick('account_id', 'account_id_v2'),
    )


def make_ds(query: str = '', body: str = '', salt: str = SALT_CN) -> str:
    """生成 DS 签名头。"""
    t = str(int(time.time()))
    r = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    payload = f'salt={salt}&t={t}&r={r}&b={body}&q={query}'
    h = hashlib.md5(payload.encode('utf-8')).hexdigest()
    return f'{t},{r},{h}'


def _throttle() -> None:
    """全局最小间隔。"""
    global _last_call
    with _lock:
        now = time.time()
        wait = MIN_INTERVAL - (now - _last_call)
        if wait > 0:
            time.sleep(wait)
        _last_call = time.time()


def _request(path: str, params: dict[str, str], cookie: ParsedCookie,
             client_type: str | None = None,
             app_version: str | None = None) -> dict[str, Any]:
    """发一次签名请求并返回 data 段。

    ``client_type`` / ``app_version`` 可覆盖，用于探测哪组请求头被接受
    （实测不同组合会返回不同的 retcode）。
    """
    query = urllib.parse.urlencode(sorted(params.items()))
    url = f'{HOST}{path}?{query}'
    ds = make_ds(query)

    headers = {
        'User-Agent': UA,
        'Accept': 'application/json, text/plain, */*',
        'Cookie': cookie.raw,
        'DS': ds,
        'x-rpc-app_version': app_version if app_version is not None else APP_VERSION,
        'x-rpc-client_type': client_type if client_type is not None else '5',
        'x-rpc-language': 'zh-cn',
        'Referer': 'https://app.mihoyo.com/',
        'Origin': 'https://app.mihoyo.com',
    }
    # 传空字符串表示不带这个头
    for key in [k for k, v in headers.items() if v == '']:
        headers.pop(key)

    last_err: Exception | None = None
    for attempt in range(MAX_RETRY + 1):
        _throttle()
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
                body = r.read().decode('utf-8', 'ignore')
        except urllib.error.HTTPError as e:
            last_err = MysError(f'HTTP {e.code}', e.code)
            if e.code in (403, 429):
                time.sleep(2 ** attempt)
                continue
            raise last_err from e
        except urllib.error.URLError as e:
            last_err = MysError(f'网络错误：{e.reason}')
            time.sleep(2 ** attempt)
            continue

        try:
            payload = json.loads(body)
        except json.JSONDecodeError as e:
            raise MysError('接口返回的不是 JSON') from e

        retcode = payload.get('retcode')
        if retcode == 0 and payload.get('data'):
            return payload['data']

        message = payload.get('message') or '未知错误'
        # 10041：鉴权已过，但该角色的战绩数据未公开（米游社侧隐私设置）
        if retcode == 10041:
            raise MysError(RETCODE_10041_HINT, retcode)
        # 登录态失效：直接抛，不重试
        if retcode in (10001, -100, 10103, 1009):
            raise MysError(
                f'登录态无效（{retcode} {message}）。请重新获取 Cookie 绑定。',
                retcode,
            )
        # 其它错误重试
        last_err = MysError(f'{retcode} {message}', retcode)
        if retcode in (-10001, -110):
            raise last_err  # 签名问题，重试无意义
        time.sleep(2 ** attempt)

    raise last_err or MysError('请求失败')


# 请求头候选：官方前端不同时期用不同组合，逐个试到能通为止
HEADER_VARIANTS: list[tuple[str, str, str]] = [
    # (说明, client_type, app_version)，空串表示不带该头
    ('web/2.11.1', '5', '2.11.1'),
    ('web/无版本', '5', ''),
    ('web/2.90.1', '5', '2.90.1'),
    ('app/2.90.1', '3', '2.90.1'),
    ('app/无版本', '3', ''),
    ('pc/1', '1', '1.0.0'),
    ('仅 Cookie+DS', '', ''),
]


def probe_headers(uid: str, server: str, cookie: ParsedCookie) -> tuple[str, str, dict]:
    """逐个试请求头组合，返回第一个能成功的。

    返回 ``(client_type, app_version, data)``。
    """
    errors: list[str] = []
    for label, ctype, ver in HEADER_VARIANTS:
        try:
            data = _request(PATH_INDEX, {'role_id': str(uid), 'server': server},
                            cookie, client_type=ctype, app_version=ver)
            return ctype, ver, data
        except MysError as e:
            errors.append(f'{label}: {e}')
            continue
    raise MysError('所有请求头组合都失败：\n  ' + '\n  '.join(errors))


def fetch_index(uid: str, server: str, cookie: ParsedCookie) -> dict[str, Any]:
    """玩家基础信息。"""
    return _request(PATH_INDEX, {'role_id': str(uid), 'server': server}, cookie)


def fetch_avatar_info(uid: str, server: str, cookie: ParsedCookie) -> dict[str, Any]:
    """全部角色详情（等级、星魂、光锥、遗器主副词条）。"""
    return _request(
        PATH_AVATAR,
        {'role_id': str(uid), 'server': server, 'need_wiki': 'true'},
        cookie,
    )


def fetch_challenge(uid: str, server: str, cookie: ParsedCookie,
                    schedule_type: str = '1') -> dict[str, Any]:
    """战绩：混沌回忆 / 虚构叙事 / 末日幻影。"""
    return _request(
        PATH_CHALLENGE,
        {'role_id': str(uid), 'server': server, 'schedule_type': schedule_type},
        cookie,
    )


def check_cookie(uid: str, server: str, cookie: ParsedCookie) -> dict[str, Any]:
    """校验 cookie 是否可用，返回基础信息。"""
    if not cookie.usable:
        raise MysError('Cookie 缺少 ltoken / ltuid，请确认复制完整')
    return fetch_index(uid, server, cookie)
