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


def _request(path: str, params: dict[str, str], cookie: ParsedCookie) -> dict[str, Any]:
    """发一次签名请求并返回 data 段。"""
    query = urllib.parse.urlencode(sorted(params.items()))
    url = f'{HOST}{path}?{query}'
    ds = make_ds(query)

    headers = {
        'User-Agent': UA,
        'Accept': 'application/json, text/plain, */*',
        'Cookie': cookie.raw,
        'DS': ds,
        'x-rpc-app_version': APP_VERSION,
        'x-rpc-client_type': '5',
        'x-rpc-language': 'zh-cn',
        'Referer': 'https://app.mihoyo.com/',
        'Origin': 'https://app.mihoyo.com',
    }

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
