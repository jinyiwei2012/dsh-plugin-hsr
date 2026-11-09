# -*- coding: utf-8 -*-
"""用 Pillow 把查询结果画成 PNG 卡片。

选 Pillow 而不是 Playwright 的原因：本机已有 Pillow 与中文字体，
不需要额外下载 Chromium（约 150MB），冷启动快，且无浏览器版本漂移问题。

Pillow 缺失时 ``render_card`` 返回 None，调用方退回纯文字，不影响功能。
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Any

try:
    from PIL import Image, ImageDraw, ImageFont
    _HAS_PIL = True
except ImportError:  # pragma: no cover - 环境缺 Pillow 时降级
    _HAS_PIL = False

# 画布
WIDTH = 900
PAD = 28
LINE_GAP = 6

# 配色（深色 + 金色点缀，参考游戏内 UI）
BG = (26, 29, 36)
BG_CARD = (35, 39, 48)
GOLD = (212, 177, 99)
TEXT = (232, 232, 232)
TEXT_DIM = (150, 155, 165)
TEXT_WARN = (236, 138, 120)
TEXT_OK = (130, 200, 150)
DIVIDER = (55, 60, 72)

# 评级配色
GRADE_COLOR = {
    'D': (140, 140, 140), 'C': (150, 170, 190), 'B': (120, 170, 220),
    'A': (130, 200, 150), 'S': (100, 200, 210), 'SS': (170, 160, 240),
    'SSS': (212, 177, 99), 'ACE': (240, 160, 110), 'MAX': (240, 120, 140),
}

_FONT_CANDIDATES = [
    (r'C:\Windows\Fonts\msyhbd.ttc', r'C:\Windows\Fonts\msyh.ttc'),
    (r'C:\Windows\Fonts\simhei.ttf', r'C:\Windows\Fonts\simhei.ttf'),
    ('/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc',
     '/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc'),
    ('/System/Library/Fonts/PingFang.ttc', '/System/Library/Fonts/PingFang.ttc'),
]


def available() -> bool:
    """Pillow 与中文字体是否都就绪。"""
    return _HAS_PIL and _font_paths() is not None


def _font_paths() -> tuple[str, str] | None:
    for bold, regular in _FONT_CANDIDATES:
        if os.path.exists(regular):
            return (bold if os.path.exists(bold) else regular, regular)
    return None


_font_cache: dict[tuple[int, bool], Any] = {}


def _font(size: int, bold: bool = False):
    key = (size, bold)
    if key in _font_cache:
        return _font_cache[key]
    paths = _font_paths()
    if not paths:
        raise RuntimeError('找不到中文字体')
    path = paths[0] if bold else paths[1]
    f = ImageFont.truetype(path, size)
    _font_cache[key] = f
    return f


@dataclass
class Block:
    """卡片里的一个区块。"""

    heading: str = ''
    # 右侧徽标，如 "52.4 ACE"
    badge: str = ''
    badge_color: tuple[int, int, int] | None = None
    # 键值行：(标签, 值, 颜色)
    rows: list[tuple[str, str, tuple[int, int, int] | None]] = field(default_factory=list)
    # 纯文本行（会自动换行）
    text: str = ''


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_w: int) -> list[str]:
    """按像素宽度折行（兼顾中英文）。"""
    if not text:
        return []
    lines: list[str] = []
    cur = ''
    for ch in text:
        if ch == '\n':
            lines.append(cur)
            cur = ''
            continue
        trial = cur + ch
        if draw.textlength(trial, font=font) > max_w and cur:
            lines.append(cur)
            cur = ch
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def render_card(
    title: str,
    subtitle: str,
    blocks: list[Block],
    footer: str = '',
    out_dir: str | None = None,
    filename: str | None = None,
) -> str | None:
    """渲染卡片，返回 PNG 路径；不可用时返回 None。"""
    if not available():
        return None

    f_title = _font(30, True)
    f_sub = _font(16)
    f_head = _font(19, True)
    f_body = _font(16)
    f_small = _font(14)

    # ---- 先量高度 ----
    probe = Image.new('RGB', (WIDTH, 10))
    pd = ImageDraw.Draw(probe)
    inner_w = WIDTH - PAD * 2

    def block_height(b: Block) -> int:
        h = 0
        if b.heading:
            h += 26 + 8
        if b.text:
            h += len(_wrap(pd, b.text, f_small, inner_w)) * (18 + 2) + 8
        for label, value, _ in b.rows:
            h += 22 + 4
        return h + 12

    height = PAD + 40 + 34 + 16  # title + subtitle
    for b in blocks:
        height += block_height(b) + 14
    height += 40 + PAD  # footer

    # ---- 绘制 ----
    img = Image.new('RGB', (WIDTH, max(height, 200)), BG)
    d = ImageDraw.Draw(img)

    # 顶部金色条
    d.rectangle([0, 0, WIDTH, 4], fill=GOLD)

    y = PAD
    d.text((PAD, y), title, font=f_title, fill=GOLD)
    y += 40
    if subtitle:
        d.text((PAD, y), subtitle, font=f_sub, fill=TEXT_DIM)
        y += 34
    else:
        y += 10

    for b in blocks:
        # 卡片底
        bh = block_height(b)
        d.rounded_rectangle(
            [PAD - 8, y - 6, WIDTH - PAD + 8, y + bh - 6],
            radius=10, fill=BG_CARD,
        )
        by = y + 6

        if b.heading:
            d.text((PAD + 4, by), b.heading, font=f_head, fill=TEXT)
            if b.badge:
                bw = d.textlength(b.badge, font=f_small)
                d.text(
                    (WIDTH - PAD - 12 - bw, by + 4), b.badge,
                    font=f_small, fill=b.badge_color or GOLD,
                )
            by += 26 + 8

        if b.text:
            for line in _wrap(pd, b.text, f_small, inner_w - 8):
                d.text((PAD + 4, by), line, font=f_small, fill=TEXT_DIM)
                by += 18 + 2
            by += 8

        for label, value, color in b.rows:
            d.text((PAD + 4, by), str(label), font=f_body, fill=TEXT_DIM)
            vw = d.textlength(str(value), font=f_body)
            d.text(
                (WIDTH - PAD - 12 - vw, by), str(value),
                font=f_body, fill=color or TEXT,
            )
            by += 22 + 4

        y += bh + 14

    # 分隔线 + 页脚
    d.line([PAD, y - 6, WIDTH - PAD, y - 6], fill=DIVIDER, width=1)
    d.text((PAD, y + 6), footer or f'生成于 {time.strftime("%Y-%m-%d %H:%M")}',
           font=f_small, fill=TEXT_DIM)

    # ---- 落盘 ----
    if out_dir is None:
        out_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'data', 'media',
        )
    os.makedirs(out_dir, exist_ok=True)
    name = filename or f'hsr-{int(time.time() * 1000)}.png'
    path = os.path.join(out_dir, name)
    img.save(path, 'PNG', optimize=True)
    return path


def grade_color(grade: str) -> tuple[int, int, int]:
    return GRADE_COLOR.get(grade.upper(), TEXT)
