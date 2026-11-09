# -*- coding: utf-8 -*-
"""复刻 miao-plugin 的角色面板卡（profile-detail）。

版式对齐上游 ``resources/character/profile-detail.{html,css}``：

- 立绘铺在顶部，角色名 50px 绝对定位在右上角
- ``.char-attr`` 是一张属性表：图标 / 名称 / 词条权重 / 数值 / 基础+加成
- 下方是技能图标带等级、光锥卡、遗器套装

词条权重显示与上游一致：``>=80`` 标金色（核心），否则普通色。

图片资源走社区库 Mar-7th/StarRailRes（jsDelivr）。
"""

from __future__ import annotations

import os
import time
from typing import Any

RES_CDN = 'https://cdn.jsdelivr.net/gh/Mar-7th/StarRailRes@master/'

# 与 core/artifact 的权重键对应：显示顺序、标题、图标
ATTR_ROWS = [
    ('hp', '生命值', 'IconMaxHP'),
    ('atk', '攻击力', 'IconAttack'),
    ('def', '防御力', 'IconDefence'),
    ('speed', '速度', 'IconSpeed'),
    ('cpct', '暴击率', 'IconCriticalChance'),
    ('cdmg', '暴击伤害', 'IconCriticalDamage'),
    ('dmg', '伤害加成', None),          # 用元素图标
    ('stance', '击破特攻', 'IconBreakUp'),
    ('effPct', '效果命中', 'IconStatusProbability'),
    ('effDef', '效果抵抗', 'IconStatusResistance'),
    ('heal', '治疗加成', 'IconHealRatio'),
    ('recharge', '能量恢复', 'IconEnergyRecovery'),
]

ELEMENT_ICON = {
    '物理': 'Physical', '火': 'Fire', '冰': 'Ice', '雷': 'Thunder',
    '风': 'Wind', '量子': 'Quantum', '虚数': 'Imaginary',
}

# 面板里这些是百分比字段
PERCENT_ATTRS = {'cpct', 'cdmg', 'stance', 'effPct', 'effDef', 'heal', 'recharge', 'dmg'}

_CSS = """
* { margin:0; padding:0; box-sizing:border-box; }
body { width:660px; font-family:"Microsoft YaHei","PingFang SC","Noto Sans CJK SC",sans-serif;
  font-size:16px; color:#fff; background:#191919; }
.container { width:660px; background:#191919; padding-bottom:10px; }

/* ---------- 立绘 + 右上信息 ---------- */
.basic { position:relative; }
.main-pic { width:1400px; height:520px; background-size:contain;
  background-repeat:no-repeat; background-position:center;
  margin-left:-545px; position:relative; z-index:2; }
.detail { position:absolute; right:20px; top:20px; color:#fff; z-index:3; text-align:right; }
.char-name { font-size:50px; font-weight:700; text-align:right; letter-spacing:2px;
  text-shadow:0 0 3px #000, 2px 2px 4px rgba(0,0,0,.7); }
.char-lv { text-align:right; text-shadow:0 0 3px #000, 2px 2px 4px rgba(0,0,0,.7); }
.char-lv .cons { margin-left:5px; vertical-align:bottom; display:inline-block;
  padding:0 7px; border-radius:10px; font-size:14px;
  background:rgba(0,0,0,.45); border:1px solid rgba(255,255,255,.25); }
.char-path { margin-top:6px; font-size:14px; color:#d8dbe2;
  text-shadow:0 0 3px #000, 2px 2px 4px rgba(0,0,0,.7); }

/* ---------- 属性表 ---------- */
.char-attr { list-style:none; margin:0 10px; position:relative; z-index:3;
  background:rgba(25,27,33,.88); border-radius:10px; overflow:hidden; }
.char-attr li { display:flex; align-items:center; gap:8px;
  height:34px; line-height:34px; padding:0 12px; font-size:15px; }
.char-attr li:nth-child(odd) { background:rgba(255,255,255,.035); }
.char-attr .icon { width:22px; height:22px; flex:0 0 22px;
  background-size:contain; background-repeat:no-repeat; background-position:center;
  opacity:.92; }
.char-attr .title { width:96px; flex:0 0 96px; color:#d6d9e0; }
.char-attr .weight { width:44px; flex:0 0 44px; text-align:center; font-size:13px; }
.char-attr .weight .gold { color:#ffe699; font-weight:700; }
.char-attr .weight .normal { color:#8b909c; }
.char-attr .value { flex:1; text-align:right; font-weight:700;
  font-variant-numeric:tabular-nums; }
.char-attr .value2 { width:150px; flex:0 0 150px; text-align:right; font-size:13px;
  color:#8b909c; font-variant-numeric:tabular-nums; }
.char-attr .value2 .base { color:#6f7480; }
.char-attr .value2 .plus { color:#7fd0a0; margin-left:6px; }

/* ---------- 技能 ---------- */
.sr-talent { display:flex; gap:10px; margin:12px 10px 0; position:relative; z-index:3; }
.talent-item { width:64px; text-align:center; }
/* 外层承载角标，内层负责圆形裁剪，否则等级数字会被圆角切掉 */
.talent-icon-wrap { position:relative; width:56px; height:56px; margin:0 auto; }
.talent-icon { width:100%; height:100%;
  border-radius:50%; background:rgba(30,33,40,.9);
  border:1px solid rgba(255,255,255,.14); overflow:hidden; }
.talent-icon-img { width:100%; height:100%; background-size:contain;
  background-repeat:no-repeat; background-position:center; }
.talent-icon-wrap strong { position:absolute; right:-4px; bottom:-4px;
  background:rgba(0,0,0,.88); border:1px solid rgba(255,255,255,.2);
  border-radius:8px; padding:0 5px; font-size:12px; line-height:16px;
  font-weight:700; }
.talent-item span { display:block; font-size:11px; color:#9aa0ad; margin-top:5px; }

/* ---------- 光锥 ---------- */
.sr-weapon { display:flex; gap:12px; align-items:center;
  margin:12px 10px 0; padding:10px; position:relative; z-index:3;
  background:rgba(25,27,33,.88); border-radius:10px; }
.weapon-img { width:72px; height:72px; flex:0 0 72px; border-radius:8px;
  background-size:contain; background-repeat:no-repeat; background-position:center;
  background-color:rgba(255,255,255,.05); }
.weapon-info { flex:1; }
.weapon-title { display:flex; align-items:baseline; gap:8px; }
.weapon-title strong { font-size:16px; }
.weapon-title span { font-size:13px; color:#9aa0ad; }
.weapon-sets { margin-top:6px; font-size:13px; color:#b6bac4; }

.footer { padding:8px 12px 0; font-size:11px; color:#666; }
"""


def _fmt(v: float, percent: bool) -> str:
    if percent:
        return f'{v * 100:.1f}%'
    r = round(v, 1)
    return f'{int(round(r))}' if abs(r - round(r)) < 1e-9 else f'{r:.1f}'


def _attr_lookup(char: Any) -> dict[str, tuple[float, float, float]]:
    """返回 {权重键: (数值, 基础, 加成)}。"""
    panel = getattr(char, 'panel', {}) or {}
    pbase = getattr(char, 'panel_base', {}) or {}
    padd = getattr(char, 'panel_add', {}) or {}

    elem = getattr(char, 'element', '')
    dmg_key = f'{elem}属性伤害提高'
    dmg_val = panel.get(dmg_key, 0.0)
    dmg_base = pbase.get(dmg_key, 0.0)
    dmg_add = padd.get(dmg_key, 0.0)

    mapping = {
        'hp': '生命值', 'atk': '攻击力', 'def': '防御力', 'speed': '速度',
        'cpct': '暴击率', 'cdmg': '暴击伤害', 'stance': '击破特攻',
        'effPct': '效果命中', 'effDef': '效果抵抗', 'heal': '治疗量加成',
        'recharge': '能量恢复效率',
    }
    out: dict[str, tuple[float, float, float]] = {}
    for key, cn in mapping.items():
        if cn in panel:
            out[key] = (panel[cn], pbase.get(cn, 0.0), padd.get(cn, 0.0))
    out['dmg'] = (dmg_val, dmg_base, dmg_add)
    return out


def build_panel_html(
    char: Any,
    weights: dict[str, int],
    uid: str,
    footer: str = '',
) -> str:
    """生成角色面板卡 HTML。"""
    portrait = f'{RES_CDN}{char.portrait}' if getattr(char, 'portrait', '') else ''
    bg = f"background-image:url('{portrait}')" if portrait else ''
    rank_txt = f'{char.rank}命' if getattr(char, 'rank', 0) else '0命'
    elem = getattr(char, 'element', '')
    elem_icon = ELEMENT_ICON.get(elem, '')

    vals = _attr_lookup(char)

    rows: list[str] = []
    for key, title, icon_name in ATTR_ROWS:
        if key not in vals:
            continue
        value, base, add = vals[key]
        if value == 0 and base == 0 and add == 0 and key in ('heal', 'recharge'):
            continue
        percent = key in PERCENT_ATTRS

        if icon_name:
            icon_url = f'{RES_CDN}icon/property/{icon_name}.png'
        elif elem_icon:
            icon_url = f'{RES_CDN}icon/element/{elem_icon}.png'
        else:
            icon_url = ''

        w = weights.get(key, 0)
        w_cls = 'gold' if w >= 80 else 'normal'
        w_txt = str(w) if w else ''

        base_txt = _fmt(base, percent) if base else '-'
        add_txt = _fmt(add, percent) if add else '-'
        rows.append(
            '<li>'
            f'<div class="icon" style="background-image:url(\'{icon_url}\')"></div>'
            f'<div class="title">{title}</div>'
            f'<div class="weight"><span class="{w_cls}">{w_txt}</span></div>'
            f'<div class="value">{_fmt(value, percent)}</div>'
            f'<div class="value2"><span class="base">{base_txt}</span>'
            f'<span class="plus">{("+" + add_txt) if add else "-"}</span></div>'
            '</li>'
        )

    # 技能（只取主要四个，去掉重复/秘技）
    seen_types: set[str] = set()
    talents: list[str] = []
    for s in getattr(char, 'skills', []) or []:
        t = s.get('type') or ''
        if t not in ('普攻', '战技', '终结技', '天赋'):
            continue
        if t in seen_types:
            continue
        seen_types.add(t)
        icon = s.get('icon') or ''
        icon_url = f'{RES_CDN}{icon}' if icon else ''
        talents.append(
            '<div class="talent-item">'
            '<div class="talent-icon-wrap">'
            '<div class="talent-icon">'
            f'<div class="talent-icon-img" style="background-image:url(\'{icon_url}\')"></div>'
            '</div>'
            f'<strong>{s.get("level", 0)}</strong></div>'
            f'<span>{t}</span></div>'
        )

    # 光锥
    lc = getattr(char, 'light_cone', None)
    weapon_html = ''
    if lc:
        lc_icon = lc.get('icon') or ''
        lc_url = f'{RES_CDN}{lc_icon}' if lc_icon else ''
        weapon_html = (
            '<div class="sr-weapon">'
            f'<div class="weapon-img" style="background-image:url(\'{lc_url}\')"></div>'
            '<div class="weapon-info">'
            '<div class="weapon-title">'
            f'<strong>{lc.get("name", "")}</strong>'
            f'<span>Lv.{lc.get("level", 0)}</span>'
            f'<span>叠影{lc.get("rank", 1)}阶</span>'
            '</div>'
            f'<div class="weapon-sets">套装：{_fmt_sets(char)}</div>'
            '</div></div>'
        )

    foot = footer or '角色面板 · 词条权重来自 miao-plugin'
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{_CSS}</style></head>
<body><div class="container">
  <div class="basic">
    <div class="main-pic" style="{bg}"></div>
    <div class="detail">
      <div class="char-name">{char.name}</div>
      <div class="char-lv">UID {uid} - Lv.{char.level}
        <span class="cons">{rank_txt}</span></div>
      <div class="char-path">{elem} · {getattr(char, 'path', '')}</div>
    </div>
  </div>
  <ul class="char-attr">{''.join(rows)}</ul>
  {f'<div class="sr-talent">{"".join(talents)}</div>' if talents else ''}
  {weapon_html}
  <div class="footer">{foot}</div>
</div></body></html>"""


def _fmt_sets(char: Any) -> str:
    sc = getattr(char, 'set_counts', {}) or {}
    if not sc:
        return '无'
    return ' / '.join(f'{k}×{v}' for k, v in sc.items())


def render_panel_card(
    char: Any,
    weights: dict[str, int],
    uid: str,
    out_dir: str | None = None,
    filename: str | None = None,
    footer: str = '',
) -> str | None:
    """渲染面板卡 PNG。"""
    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        return None

    html = build_panel_html(char, weights, uid, footer=footer)
    if out_dir is None:
        out_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            'data', 'media',
        )
    os.makedirs(out_dir, exist_ok=True)
    name = filename or f'hsr-panel-{int(time.time() * 1000)}.png'
    path = os.path.join(out_dir, name)

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=['--no-sandbox', '--disable-dev-shm-usage'])
            try:
                page = browser.new_page(
                    viewport={'width': 660, 'height': 900},
                    device_scale_factor=2,
                )
                page.set_content(html, wait_until='networkidle', timeout=25000)
                page.wait_for_timeout(350)
                el = page.query_selector('.container') or page
                el.screenshot(path=path)
            finally:
                browser.close()
        return path if os.path.isfile(path) else None
    except Exception:
        return None
