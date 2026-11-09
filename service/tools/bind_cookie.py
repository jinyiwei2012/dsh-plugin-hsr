# -*- coding: utf-8 -*-
"""本地 Cookie 绑定工具。

Cookie **不会**经过对话、不会写日志、不会进 git —— 直接写入本机 SQLite。

用法::

    python service/tools/bind_cookie.py                  # 交互式绑定
    python service/tools/bind_cookie.py --uid 114172341  # 带 UID
    python service/tools/bind_cookie.py --list           # 查看已绑定
    python service/tools/bind_cookie.py --delete 114172341

获取 Cookie 的步骤见 docs/cookie.md。
"""

from __future__ import annotations

import argparse
import getpass
import os
import sys

_SERVICE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _SERVICE)

from hsr.api.mys import MysError, check_cookie, parse_cookie  # noqa: E402
from hsr.store import db  # noqa: E402

SERVERS = {
    '1': ('prod_gf_cn', '国服'),
    '2': ('prod_official_asia', '国际服 Asia'),
    '3': ('prod_official_usa', '国际服 America'),
    '4': ('prod_official_eur', '国际服 Europe'),
    '5': ('prod_official_cht', '国际服 TW/HK/MO'),
}


def _mask(s: str, keep: int = 4) -> str:
    if not s:
        return '(空)'
    if len(s) <= keep * 2:
        return '*' * len(s)
    return f'{s[:keep]}{"*" * 6}{s[-keep:]}'


def cmd_list() -> int:
    accounts = db.list_accounts()
    if not accounts:
        print('还没有绑定任何账号。运行 `python service/tools/bind_cookie.py` 绑定。')
        return 0
    default = db.get_setting('default_uid')
    print(f'已绑定 {len(accounts)} 个账号（数据库: {db.DB_PATH}）\n')
    for a in accounts:
        mark = ' ← 默认' if a.uid == default else ''
        nick = a.nickname or '(未校验)'
        print(f'  UID {a.uid}  {nick}  Lv{a.level or "?"}  '
              f'服务器 {a.server}{mark}')
    return 0


def cmd_delete(uid: str) -> int:
    if db.delete_account(uid):
        print(f'已删除 UID {uid} 的绑定。')
        return 0
    print(f'没有找到 UID {uid}。')
    return 1


def _ask_server() -> str:
    print('\n选择服务器：')
    for k, (_, label) in SERVERS.items():
        print(f'  {k}. {label}')
    raw = input('输入序号（直接回车 = 1 国服）: ').strip() or '1'
    return SERVERS.get(raw, SERVERS['1'])[0]


def cmd_bind(uid: str | None) -> int:
    print('=' * 60)
    print('星穹铁道 · 米游社 Cookie 绑定')
    print('=' * 60)
    print('Cookie 只会写入本机数据库，不会上传、不会被记录到日志。')
    print('获取方法见 docs/cookie.md')
    print()

    if not uid:
        uid = input('游戏 UID（例如 114172341）: ').strip()
    if not uid.isdigit():
        print(f'UID 不合法：{uid!r}')
        return 1

    server = _ask_server()

    print()
    print('粘贴 Cookie 后回车（输入内容不会回显）：')
    try:
        cookie_raw = getpass.getpass('Cookie: ').strip()
    except (KeyboardInterrupt, EOFError):
        print('\n已取消。')
        return 1

    if not cookie_raw:
        print('Cookie 为空，已取消。')
        return 1

    parsed = parse_cookie(cookie_raw)
    print()
    print(f'  解析结果: ltuid={_mask(parsed.ltuid)}  '
          f'ltoken={_mask(parsed.ltoken)}  '
          f'cookie_token={_mask(parsed.cookie_token)}')
    if not parsed.usable:
        print('⚠️  Cookie 里没有找到 ltoken / ltuid。')
        print('   请确认复制的是已登录状态的完整 Cookie（含 ltoken 与 ltuid）。')
        return 1

    print('\n正在校验……')
    try:
        data = check_cookie(uid, server, parsed)
    except MysError as e:
        print(f'❌ 校验失败：{e}')
        print('   常见原因：Cookie 过期、复制不完整、UID 与服务器不匹配。')
        return 1
    except Exception as e:  # noqa: BLE001
        print(f'❌ 校验异常：{type(e).__name__}: {e}')
        return 1

    role = data.get('role') or {}
    nickname = role.get('nickname') or ''
    level = int(role.get('level') or 0)

    db.save_account(uid, cookie_raw, server=server, nickname=nickname, level=level)
    print()
    print('✅ 绑定成功')
    print(f'   UID {uid}  {nickname}  Lv{level}')
    print(f'   数据库: {db.DB_PATH}')
    print()
    print('接下来可以试：')
    print('   python service/tools/query.py 查询')
    print('   python service/tools/query.py 昔涟遗器')
    return 0


def cmd_uid_only(uid: str) -> int:
    """只登记 UID，不绑 Cookie —— 走 mihomo 公开接口，仅能看展柜角色。"""
    if not uid.isdigit():
        print(f'UID 不合法：{uid!r}')
        return 1
    db.set_default_uid(uid)
    print('✅ 已登记 UID（未绑定 Cookie）')
    print(f'   UID {uid}')
    print('   数据源: mihomo 公开接口，只能看到游戏展柜里展示的角色。')
    print('   想查全部角色请重新运行本工具并绑定 Cookie。')
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description='星穹铁道 Cookie 绑定')
    ap.add_argument('--uid', help='游戏 UID')
    ap.add_argument('--uid-only', metavar='UID',
                    help='只登记 UID，不绑 Cookie（走 mihomo，仅展柜）')
    ap.add_argument('--list', action='store_true', help='列出已绑定账号')
    ap.add_argument('--delete', metavar='UID', help='删除指定 UID 的绑定')
    args = ap.parse_args(argv)

    if args.list:
        return cmd_list()
    if args.delete:
        return cmd_delete(args.delete)
    if args.uid_only:
        return cmd_uid_only(args.uid_only)
    return cmd_bind(args.uid)


if __name__ == '__main__':
    raise SystemExit(main())
