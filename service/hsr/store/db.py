# -*- coding: utf-8 -*-
"""本地 SQLite 存储：cookie、面板缓存、设置。

数据库文件默认位于 ``service/data/hsr.db``，只在本机使用，不上传。

安全约定
--------
- cookie 只写入本库，不写日志、不回显、不进 git（``service/data/`` 已忽略）
- 读取时按 uid 区分账号；同一 uid 重复绑定时覆盖
"""

from __future__ import annotations

import json
import os
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.environ.get('HSR_DATA_DIR') or os.path.join(_ROOT, 'data')
DB_PATH = os.path.join(DATA_DIR, 'hsr.db')

SCHEMA = """
CREATE TABLE IF NOT EXISTS account (
    uid         TEXT PRIMARY KEY,
    cookie      TEXT NOT NULL,
    server      TEXT NOT NULL DEFAULT 'prod_gf_cn',
    nickname    TEXT,
    level       INTEGER,
    created_at  INTEGER NOT NULL,
    updated_at  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS profile_cache (
    uid         TEXT PRIMARY KEY,
    payload     TEXT NOT NULL,
    fetched_at  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS setting (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL,
    updated_at  INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS command_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    uid         TEXT,
    command     TEXT NOT NULL,
    ok          INTEGER NOT NULL,
    elapsed_ms  INTEGER,
    created_at  INTEGER NOT NULL
);
"""


def ensure_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """打开数据库连接（自动建表）。"""
    ensure_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()


@dataclass
class Account:
    """一个已绑定的米游社账号。"""

    uid: str
    cookie: str
    server: str
    nickname: str = ''
    level: int = 0
    updated_at: int = 0


def save_account(uid: str, cookie: str, server: str = 'prod_gf_cn',
                 nickname: str = '', level: int = 0) -> None:
    """保存或更新账号绑定。"""
    now = int(time.time())
    with connect() as c:
        c.execute(
            """INSERT INTO account (uid, cookie, server, nickname, level, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(uid) DO UPDATE SET
                 cookie=excluded.cookie,
                 server=excluded.server,
                 nickname=COALESCE(NULLIF(excluded.nickname,''), account.nickname),
                 level=CASE WHEN excluded.level>0 THEN excluded.level ELSE account.level END,
                 updated_at=excluded.updated_at""",
            (str(uid), cookie, server, nickname, level, now, now),
        )
        c.execute(
            "INSERT INTO setting (key, value, updated_at) VALUES ('default_uid', ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (str(uid), now),
        )


def get_account(uid: str | None = None) -> Account | None:
    """取账号；uid 为空时取默认账号。"""
    with connect() as c:
        if not uid:
            row = c.execute("SELECT value FROM setting WHERE key='default_uid'").fetchone()
            uid = row['value'] if row else None
        if not uid:
            return None
        row = c.execute("SELECT * FROM account WHERE uid=?", (str(uid),)).fetchone()
    if not row:
        return None
    return Account(
        uid=row['uid'], cookie=row['cookie'], server=row['server'],
        nickname=row['nickname'] or '', level=row['level'] or 0,
        updated_at=row['updated_at'],
    )


def list_accounts() -> list[Account]:
    """列出全部绑定账号。"""
    with connect() as c:
        rows = c.execute("SELECT * FROM account ORDER BY updated_at DESC").fetchall()
    return [
        Account(uid=r['uid'], cookie=r['cookie'], server=r['server'],
                nickname=r['nickname'] or '', level=r['level'] or 0,
                updated_at=r['updated_at'])
        for r in rows
    ]


def delete_account(uid: str) -> bool:
    """删除账号绑定。"""
    with connect() as c:
        cur = c.execute("DELETE FROM account WHERE uid=?", (str(uid),))
        c.execute("DELETE FROM profile_cache WHERE uid=?", (str(uid),))
        return cur.rowcount > 0


def get_default_uid() -> str:
    """当前默认 UID（有无 cookie 都适用）。"""
    with connect() as c:
        row = c.execute("SELECT value FROM setting WHERE key='default_uid'").fetchone()
    return row['value'] if row else ''


def set_default_uid(uid: str) -> None:
    with connect() as c:
        c.execute(
            "INSERT INTO setting (key, value, updated_at) VALUES ('default_uid', ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (str(uid), int(time.time())),
        )


def save_profile(uid: str, payload: dict[str, Any]) -> None:
    """缓存一次拉取到的面板数据。"""
    with connect() as c:
        c.execute(
            "INSERT INTO profile_cache (uid, payload, fetched_at) VALUES (?, ?, ?) "
            "ON CONFLICT(uid) DO UPDATE SET payload=excluded.payload, fetched_at=excluded.fetched_at",
            (str(uid), json.dumps(payload, ensure_ascii=False), int(time.time())),
        )


def load_profile(uid: str, max_age: int | None = None) -> dict[str, Any] | None:
    """读取缓存面板；超过 max_age 秒视为过期。"""
    with connect() as c:
        row = c.execute("SELECT payload, fetched_at FROM profile_cache WHERE uid=?",
                        (str(uid),)).fetchone()
    if not row:
        return None
    if max_age is not None and int(time.time()) - row['fetched_at'] > max_age:
        return None
    try:
        return json.loads(row['payload'])
    except json.JSONDecodeError:
        return None


def get_setting(key: str, default: str = '') -> str:
    with connect() as c:
        row = c.execute("SELECT value FROM setting WHERE key=?", (key,)).fetchone()
    return row['value'] if row else default


def set_setting(key: str, value: str) -> None:
    with connect() as c:
        c.execute(
            "INSERT INTO setting (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at",
            (key, value, int(time.time())),
        )


def log_command(uid: str, command: str, ok: bool, elapsed_ms: int) -> None:
    with connect() as c:
        c.execute(
            "INSERT INTO command_log (uid, command, ok, elapsed_ms, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (uid or '', command[:200], 1 if ok else 0, elapsed_ms, int(time.time())),
        )
