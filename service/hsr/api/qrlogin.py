# -*- coding: utf-8 -*-
"""米游社扫码登录。

流程
----
1. ``create_qr()``            -> 拿 ticket 与二维码内容（一个 URL）
2. 用户用米游社 App 扫码并确认
3. ``poll_status(ticket)``    -> 轮询直到 ``Confirmed``，返回 token 列表
4. ``build_cookie(tokens)``   -> 拼成可用 Cookie 串

接口
----
``POST https://passport-api.mihoyo.com/account/ma-cn-passport/app/createQRLogin``
``POST https://passport-api.mihoyo.com/account/ma-cn-passport/app/queryQRLoginStatus``

请求头里的 ``x-rpc-app_id`` / ``client_type`` / ``app_version`` 三项缺一不可，
否则返回 ``-3001 参数不合法``；``app_id`` 也可以放在请求体里。

风险提示
--------
非官方接口。扫码登录等同于用你的账号密码登录，请只在本机使用，
不要把 ticket 或拿到的 Cookie 发给任何人。
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable

HOST = 'https://passport-api.mihoyo.com'
PATH_CREATE = '/account/ma-cn-passport/app/createQRLogin'
PATH_STATUS = '/account/ma-cn-passport/app/queryQRLoginStatus'

APP_ID = 'bll8iq97cem8'
APP_VERSION = '2.90.1'
APP_UA = 'Mozilla/5.0 miHoYoBBS/2.90.1 Capture/2.2.0'
DEVICE_ID = '00000000000000000000000000000000'
DEVICE_FP = '38d7fa104e5d7'
TIMEOUT = 25

# token_type -> cookie 字段名
# 实测：App 扫码只返回 token_type=1（长度约 148），那是 **stoken**，
# 不是 ltoken。真要用 stoken 换出 ltoken / cookie_token 才行，
# 见下方 derive_cookie_by_stoken()。
TOKEN_TYPE_MAP = {
    1: 'stoken',
    2: 'ltoken',
    3: 'cookie_token',
}

# 用 stoken 换其它凭据的接口
URL_LTOKEN = '/account/auth/api/getLTokenBySToken'
URL_COOKIE_TOKEN = '/account/auth/api/getCookieAccountInfoBySToken'


class QRLoginError(RuntimeError):
    """扫码登录失败。"""


@dataclass
class QRCode:
    """一张待扫描的二维码。"""

    ticket: str
    url: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class QRStatus:
    """轮询到的状态。"""

    status: str
    tokens: list[dict[str, Any]] = field(default_factory=list)
    user_info: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def confirmed(self) -> bool:
        return self.status.lower() == 'confirmed'

    @property
    def expired(self) -> bool:
        return self.status.lower() in ('expired', 'invalid', 'cancelled', 'canceled')


def _headers() -> dict[str, str]:
    return {
        'User-Agent': APP_UA,
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'x-rpc-app_id': APP_ID,
        'x-rpc-client_type': '3',
        'x-rpc-app_version': APP_VERSION,
        'x-rpc-device_id': DEVICE_ID,
        'x-rpc-device_fp': DEVICE_FP,
    }


def _post(path: str, body: dict[str, Any], timeout: int = TIMEOUT) -> dict[str, Any]:
    url = HOST + path
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode('utf-8'),
        headers=_headers(),
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            text = r.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        raise QRLoginError(f'HTTP {e.code}') from e
    except urllib.error.URLError as e:
        raise QRLoginError(f'网络错误：{e.reason}') from e

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as e:
        raise QRLoginError('接口返回的不是 JSON') from e

    retcode = payload.get('retcode')
    if retcode != 0:
        msg = payload.get('message') or '未知错误'
        if retcode == -3001:
            raise QRLoginError(
                f'{msg}（{retcode}）。通常是请求头里的 x-rpc-* 参数不被接受，'
                '官方可能调整了 app_id 或版本号。'
            )
        raise QRLoginError(f'{msg}（{retcode}）')
    return payload.get('data') or {}


def _get_with_cookie(path: str, cookie: str, timeout: int = TIMEOUT) -> dict[str, Any]:
    """带 Cookie 的 GET 请求（用于 stoken 换 ltoken）。"""
    url = HOST + path
    headers = {
        'User-Agent': APP_UA,
        'Accept': 'application/json',
        'Cookie': cookie,
        'x-rpc-app_id': APP_ID,
        'x-rpc-client_type': '3',
        'x-rpc-app_version': APP_VERSION,
    }
    req = urllib.request.Request(url, headers=headers, method='GET')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            text = r.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        raise QRLoginError(f'HTTP {e.code}') from e
    except urllib.error.URLError as e:
        raise QRLoginError(f'网络错误：{e.reason}') from e

    try:
        payload = json.loads(text)
    except json.JSONDecodeError as e:
        raise QRLoginError('接口返回的不是 JSON') from e

    if payload.get('retcode') != 0:
        raise QRLoginError(
            f'换票失败：{payload.get("message")}（{payload.get("retcode")}）')
    return payload.get('data') or {}


def derive_cookie_by_stoken(stoken: str, mid: str = '') -> dict[str, str]:
    """用 stoken 换出 ltoken 与 cookie_token。

    App 扫码只给 stoken，而战绩接口需要 ltoken + ltuid。
    返回可直接拼成 Cookie 的字段字典。
    """
    if not stoken:
        raise QRLoginError('stoken 为空')

    # Cookie 里 stoken 的键名随版本变化，两种都试
    candidates = [
        f'stoken={stoken}',
        f'stoken_v2={stoken}',
    ]
    if mid:
        candidates = [c + f'; mid={mid}' for c in candidates] + candidates

    last_err: Exception | None = None
    for ck in candidates:
        try:
            data = _get_with_cookie(URL_LTOKEN, ck)
        except QRLoginError as e:
            last_err = e
            continue
        ltoken = data.get('ltoken') or ''
        ltuid = str(data.get('ltuid') or data.get('uid') or '')
        if not ltoken:
            last_err = QRLoginError('换票接口没有返回 ltoken')
            continue

        out = {'ltoken': ltoken}
        if ltuid:
            out['ltuid'] = ltuid

        # 再换 cookie_token（拿不到不致命）
        try:
            info = _get_with_cookie(URL_COOKIE_TOKEN, ck)
            ct = info.get('cookie_token') or ''
            uid = str(info.get('uid') or info.get('account_id') or '')
            if ct:
                out['cookie_token'] = ct
            if uid and 'ltuid' not in out:
                out['ltuid'] = uid
        except QRLoginError:
            pass

        return out

    raise QRLoginError(f'用 stoken 换 ltoken 失败：{last_err}')


def create_qr(timeout: int = TIMEOUT) -> QRCode:
    """创建一张扫码登录二维码。"""
    data = _post(PATH_CREATE, {'app_id': APP_ID}, timeout=timeout)
    ticket = data.get('ticket')
    if not ticket:
        raise QRLoginError('接口没有返回 ticket')
    return QRCode(ticket=ticket, url=data.get('url') or '', raw=data)


def query_status(ticket: str, timeout: int = TIMEOUT) -> QRStatus:
    """查询一次扫码状态。"""
    data = _post(PATH_STATUS, {'ticket': ticket, 'app_id': APP_ID}, timeout=timeout)
    return QRStatus(
        status=str(data.get('status') or ''),
        tokens=list(data.get('tokens') or []),
        user_info=dict(data.get('user_info') or {}),
        raw=data,
    )


def poll_status(
    ticket: str,
    interval: float = 2.0,
    timeout: float = 180.0,
    on_status: Callable[[QRStatus], None] | None = None,
) -> QRStatus:
    """轮询到确认或超时。"""
    deadline = time.time() + timeout
    last = ''
    while time.time() < deadline:
        st = query_status(ticket)
        if st.status != last:
            last = st.status
            if on_status:
                on_status(st)
        if st.confirmed or st.expired:
            return st
        time.sleep(interval)
    raise QRLoginError(f'等待扫码超时（{int(timeout)} 秒）')


def build_cookie(status: QRStatus) -> str:
    """把扫码拿到的 token 拼成 Cookie 串。

    App 扫码实测只返回 ``token_type=1``（stoken），此时会再调
    ``getLTokenBySToken`` 换出 ltoken 与 cookie_token —— 战绩接口需要
    ltoken + ltuid，只给 stoken 是用不了的。
    """
    if not status.confirmed:
        raise QRLoginError(f'当前状态是 {status.status}，还没有确认')

    jar: dict[str, str] = {}
    for item in status.tokens:
        try:
            ttype = int(item.get('token_type') or 0)
        except (TypeError, ValueError):
            continue
        name = TOKEN_TYPE_MAP.get(ttype)
        token = item.get('token')
        if name and token:
            jar[name] = str(token)

    if not jar:
        raise QRLoginError('扫码结果里没有任何 token')

    # 只有 stoken 时先换票
    if not jar.get('ltoken') and jar.get('stoken'):
        mid = str(status.user_info.get('mid') or '')
        derived = derive_cookie_by_stoken(jar['stoken'], mid)
        for k, v in derived.items():
            if v:
                jar[k] = v

    if not jar.get('ltoken'):
        raise QRLoginError(
            '扫码结果里没有 ltoken，且用 stoken 换取也失败。'
            f'（拿到 {len(status.tokens)} 个 token，'
            f'类型 {[t.get("token_type") for t in status.tokens]}）'
        )

    # ltuid 优先用换票接口返回的；否则退回扫码 user_info 里的 aid
    ltuid = jar.get('ltuid') or ''
    if not ltuid:
        for key in ('aid', 'account_id', 'mid', 'uid'):
            if status.user_info.get(key):
                ltuid = str(status.user_info[key])
                break

    parts: list[str] = []
    if ltuid:
        parts.append(f'ltuid={ltuid}')
        parts.append(f'account_id={ltuid}')
    parts.append(f'ltoken={jar["ltoken"]}')
    if jar.get('cookie_token'):
        parts.append(f'cookie_token={jar["cookie_token"]}')
    # stoken 本身也一并保留，部分接口会用到
    if jar.get('stoken'):
        parts.append(f'stoken={jar["stoken"]}')
    return '; '.join(parts)


def render_qr_png(url: str, path: str) -> str | None:
    """把二维码画成 PNG，返回路径；缺少二维码库时返回 None。

    依赖 ``qrcode`` 与 ``Pillow``（见 service/requirements.txt）。
    没装时由调用方退回「打印链接」。
    """
    try:
        import qrcode  # type: ignore
        from qrcode.constants import ERROR_CORRECT_M as _EC  # type: ignore
    except ImportError:
        return None

    try:
        qr = qrcode.QRCode(version=None, error_correction=_EC, box_size=8, border=3)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        img.save(path)
        return path
    except Exception:
        return None


def qr_available() -> bool:
    """是否能渲染二维码图片。"""
    try:
        import qrcode  # type: ignore  # noqa: F401
        import PIL  # type: ignore  # noqa: F401

        return True
    except ImportError:
        return False
