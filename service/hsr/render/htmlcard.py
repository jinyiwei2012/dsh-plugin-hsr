# -*- coding: utf-8 -*-
"""用 Playwright 渲染 HTML 卡片（主路径）。

相比 Pillow 直接画像素，HTML+CSS 能做出更接近游戏 UI 的效果：
渐变、阴影、圆角、更细的字重控制，都交给浏览器。

依赖 ``playwright`` 与已安装的 chromium；不可用时由调用方退回 Pillow。
"""

from __future__ import annotations

import os
import time
from typing import Any

from .card import Block

# 深色 + 金色，参考游戏内 UI
_CSS = """
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  background: #14161c;
  font-family: "Microsoft YaHei", "PingFang SC", "Noto Sans CJK SC", sans-serif;
  color: #e8e8e8;
  padding: 0;
}
.card {
  width: 900px;
  background: linear-gradient(180deg, #1a1d24 0%, #161920 100%);
  border-top: 4px solid #d4b163;
  padding: 26px 28px 20px;
}
.title {
  font-size: 30px; font-weight: 700; color: #d4b163;
  letter-spacing: 1px;
}
.subtitle {
  font-size: 15px; color: #8b909c; margin-top: 6px;
}
.head {
  display: flex; align-items: baseline; justify-content: space-between;
  gap: 16px;
}
.badge {
  font-size: 15px; font-weight: 700; white-space: nowrap;
}
.blocks { margin-top: 18px; }
.block {
  background: #232730;
  border-radius: 10px;
  padding: 12px 16px 10px;
  margin-bottom: 12px;
  border: 1px solid rgba(255,255,255,.04);
}
.block-head {
  display: flex; align-items: baseline; justify-content: space-between;
  gap: 12px; margin-bottom: 6px;
}
.block-title {
  font-size: 18px; font-weight: 700; color: #f0f0f0;
}
.block-badge { font-size: 14px; font-weight: 700; white-space: nowrap; }
.block-text {
  font-size: 13px; line-height: 1.7; color: #8b909c;
  white-space: pre-wrap; word-break: break-word;
}
.row {
  display: flex; align-items: baseline; justify-content: space-between;
  gap: 16px; padding: 3px 0;
  border-bottom: 1px solid rgba(255,255,255,.03);
}
.row:last-child { border-bottom: none; }
.row-k { font-size: 14px; color: #8b909c; }
.row-v { font-size: 14px; color: #e8e8e8; font-variant-numeric: tabular-nums; }
.foot {
  margin-top: 14px; padding-top: 10px;
  border-top: 1px solid #373c48;
  font-size: 12px; color: #6b7280;
}
"""


def _rgb(t: tuple[int, int, int] | None, default: str) -> str:
    if not t:
        return default
    return f'rgb({t[0]},{t[1]},{t[2]})'


def _esc(s: Any) -> str:
    return (
        str(s)
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;')
        .replace('"', '&quot;')
    )


def build_html(
    title: str,
    subtitle: str,
    blocks: list[Block],
    footer: str = '',
) -> str:
    """把区块组装成完整 HTML。"""
    parts: list[str] = []
    for b in blocks:
        inner: list[str] = []
        if b.heading or b.badge:
            head = f'<div class="block-title">{_esc(b.heading)}</div>' if b.heading else '<div></div>'
            badge = ''
            if b.badge:
                color = _rgb(getattr(b, 'badge_color', None), '#d4b163')
                badge = f'<div class="block-badge" style="color:{color}">{_esc(b.badge)}</div>'
            inner.append(f'<div class="block-head">{head}{badge}</div>')
        if b.text:
            inner.append(f'<div class="block-text">{_esc(b.text)}</div>')
        for label, value, color in b.rows:
            vc = _rgb(color, '#e8e8e8')
            inner.append(
                '<div class="row">'
                f'<div class="row-k">{_esc(label)}</div>'
                f'<div class="row-v" style="color:{vc}">{_esc(value)}</div>'
                '</div>'
            )
        parts.append('<div class="block">' + ''.join(inner) + '</div>')

    foot = footer or time.strftime('生成于 %Y-%m-%d %H:%M')
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        f'<style>{_CSS}</style></head><body><div class="card">'
        '<div class="head"><div>'
        f'<div class="title">{_esc(title)}</div>'
        + (f'<div class="subtitle">{_esc(subtitle)}</div>' if subtitle else '')
        + '</div></div>'
        f'<div class="blocks">{"".join(parts)}</div>'
        f'<div class="foot">{_esc(foot)}</div>'
        '</div></body></html>'
    )


def available() -> bool:
    """Playwright 与 chromium 是否可用。"""
    try:
        import playwright  # type: ignore  # noqa: F401
    except ImportError:
        return False
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        return False
    # 有 python 包不代表浏览器装好；启动一次太贵，交给调用方在失败时回退
    return True


def render_html_to_png(
    html: str,
    path: str,
    width: int = 900,
    timeout_ms: int = 30000,
) -> str | None:
    """用 chromium 把 HTML 截图成 PNG。失败返回 None。"""
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=['--no-sandbox', '--disable-dev-shm-usage'])
            try:
                page = browser.new_page(
                    viewport={'width': width, 'height': 800},
                    device_scale_factor=2,   # 2x 更清晰
                )
                page.set_content(html, wait_until='load')
                page.wait_for_timeout(120)   # 让字体与布局稳定
                el = page.query_selector('.card') or page
                el.screenshot(path=path)
            finally:
                browser.close()
        return path if os.path.isfile(path) else None
    except Exception:
        return None


def render_card(
    title: str,
    subtitle: str,
    blocks: list[Block],
    footer: str = '',
    out_dir: str | None = None,
    filename: str | None = None,
) -> str | None:
    """渲染整张卡片，返回 PNG 路径；不可用时返回 None。"""
    if not blocks:
        return None
    html = build_html(title, subtitle, blocks, footer)

    if out_dir is None:
        out_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'data', 'media',
        )
    os.makedirs(out_dir, exist_ok=True)
    name = filename or f'hsr-{int(time.time() * 1000)}.png'
    return render_html_to_png(html, os.path.join(out_dir, name))
