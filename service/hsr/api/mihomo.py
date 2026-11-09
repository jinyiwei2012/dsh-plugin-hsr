# -*- coding: utf-8 -*-
"""mihomo 公开接口客户端与数据适配。

接口：https://api.mihomo.me/sr_info_parsed/<uid>?lang=cn
无需登录，但**只能拿到展柜里的角色**。

本模块把 mihomo 的 JSON 转成本项目统一的 ``Character`` / ``Artifact`` 模型。
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

from ..core.artifact import Artifact, SubAffix
from ..data.attr_meta import ATTR_MAP, ELEMENT_FIELD, affix_to_key, element_field_of

API = 'https://api.mihomo.me/sr_info_parsed/{uid}?lang=cn'
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) dsh-plugin-hsr'
TIMEOUT = 30


class MihomoError(RuntimeError):
    """mihomo 请求或解析失败。"""


@dataclass
class Character:
    """展柜里的一个角色（含面板与遗器）。"""

    id: str
    name: str
    rarity: int
    rank: int
    level: int
    path: str
    element: str
    base_attr: dict[str, float] = field(default_factory=dict)
    light_cone: dict | None = None
    artifacts: list[Artifact] = field(default_factory=list)
    set_counts: dict[str, int] = field(default_factory=dict)
    skills: list[dict] = field(default_factory=list)
    # 汇总面板（来自 additions）
    panel: dict[str, float] = field(default_factory=dict)
    # 立绘与图标（相对 StarRailRes 的路径）
    portrait: str = ''
    preview: str = ''
    icon: str = ''


@dataclass
class Player:
    """账号整体信息。"""

    uid: str
    nickname: str
    level: int
    world_level: int
    signature: str = ''
    avatar_id: str = ''
    avatar_name: str = ''
    stats: dict[str, Any] = field(default_factory=dict)
    characters: list[Character] = field(default_factory=list)


def _to_number(affix: dict, percent_units: bool = True) -> float:
    """把接口数值统一成「百分比用 100 为单位、平值用原值」。

    mihomo 的百分比是小数（0.648），而词条定义用 64.8，需要 ×100。
    """
    raw = affix.get('value')
    if raw is None:
        return 0.0
    try:
        val = float(raw)
    except (TypeError, ValueError):
        return 0.0
    if affix.get('percent') and percent_units:
        return val * 100.0
    return val


def _element_field(element_name: str) -> str:
    """中文属性名 -> 伤害主词条 field。"""
    return ELEMENT_FIELD.get(element_name, '')


def _parse_artifact(raw: dict, pos: int, char_element: str) -> Artifact:
    """把一件遗器 JSON 转成 Artifact。"""
    main = raw.get('main_affix') or {}
    main_type = main.get('type') or ''
    main_field = main.get('field') or ''

    # 元素伤害主词条：只有与角色属性一致时才享受 dmg 权重
    elem_field = element_field_of(main_type, main_field)
    if elem_field:
        want = _element_field(char_element)
        main_key = 'dmg' if elem_field == want else f'__elem__{elem_field}'
    else:
        main_key = affix_to_key(main_type, main_field)

    subs: list[SubAffix] = []
    for s in raw.get('sub_affix') or []:
        key = affix_to_key(s.get('type') or '', s.get('field') or '')
        if not key:
            continue
        subs.append(SubAffix(
            key=key,
            value=_to_number(s),
            count=int(s.get('count') or 1),
            name=s.get('name') or '',
        ))

    return Artifact(
        pos=pos,
        name=raw.get('name') or '',
        set_name=raw.get('set_name') or '',
        level=int(raw.get('level') or 0),
        rarity=int(raw.get('rarity') or 5),
        main_key=main_key,
        main_value=_to_number(main),
        main_name=main.get('name') or '',
        subs=subs,
        icon=raw.get('icon') or '',
    )


def _parse_character(raw: dict) -> Character:
    """把一个角色 JSON 转成 Character。"""
    element = (raw.get('element') or {}).get('name') or ''
    path = (raw.get('path') or {}).get('name') or ''

    # 角色自身基础属性
    base: dict[str, float] = {}
    for a in raw.get('attributes') or []:
        name = a.get('name') or ''
        val = a.get('value')
        if val is None:
            continue
        if name == '基础生命值':
            base['hp'] = float(val)
        elif name == '基础攻击力':
            base['atk'] = float(val)
        elif name == '基础防御力':
            base['def'] = float(val)
        elif name == '速度':
            base['speed'] = float(val)
        elif name == '暴击率':
            base['crit_rate'] = float(val)
        elif name == '暴击伤害':
            base['crit_dmg'] = float(val)

    # 养成加成（含光锥与遗器）
    add: dict[str, float] = {}
    for a in raw.get('additions') or []:
        name = a.get('name') or ''
        val = a.get('value')
        if val is not None:
            add[name] = float(val)

    # 面板 = 基础 + 加成（此前只取了加成，导致面板偏低）
    panel: dict[str, float] = {}
    for key, base_key, add_key in (
        ('生命值', 'hp', '基础生命值'),
        ('攻击力', 'atk', '基础攻击力'),
        ('防御力', 'def', '基础防御力'),
        ('速度', 'speed', '速度'),
        ('暴击率', 'crit_rate', '暴击率'),
        ('暴击伤害', 'crit_dmg', '暴击伤害'),
    ):
        if base_key in base or add_key in add:
            panel[key] = base.get(base_key, 0.0) + add.get(add_key, 0.0)
    # 这几项没有基础值，只有加成
    for key in ('击破特攻', '效果命中', '效果抵抗', '能量恢复效率', '治疗量加成'):
        if key in add:
            panel[key] = add[key]
    # 属性伤害加成（名字随属性变化，原样保留）
    for key, val in add.items():
        if key.endswith('属性伤害提高') or key.endswith('属性伤害加成'):
            panel[key] = val

    # 遗器：接口按类型给出，位置取 type（1~6）
    artifacts: list[Artifact] = []
    for r in raw.get('relics') or []:
        pos = int(r.get('type') or 0)
        if not 1 <= pos <= 6:
            continue
        artifacts.append(_parse_artifact(r, pos, element))
    artifacts.sort(key=lambda x: x.pos)

    set_counts: dict[str, int] = {}
    for r in raw.get('relics') or []:
        sn = r.get('set_name') or ''
        if sn:
            set_counts[sn] = set_counts.get(sn, 0) + 1

    skills = []
    for s in raw.get('skills') or []:
        t = s.get('type_text') or ''
        if not t:
            continue
        skills.append({
            'type': t,
            'name': s.get('name') or '',
            'level': int(s.get('level') or 0),
            'max_level': int(s.get('max_level') or 0),
        })

    lc = raw.get('light_cone') or None
    if lc:
        lc = {
            'name': lc.get('name') or '',
            'rarity': int(lc.get('rarity') or 0),
            'rank': int(lc.get('rank') or 0),
            'level': int(lc.get('level') or 0),
        }

    return Character(
        id=str(raw.get('id') or ''),
        name=raw.get('name') or '',
        rarity=int(raw.get('rarity') or 0),
        rank=int(raw.get('rank') or 0),
        level=int(raw.get('level') or 0),
        path=path,
        element=element,
        base_attr=base,
        light_cone=lc,
        artifacts=artifacts,
        set_counts=set_counts,
        skills=skills,
        panel=panel,
        portrait=raw.get('portrait') or '',
        preview=raw.get('preview') or '',
        icon=raw.get('icon') or '',
    )


def fetch_player(uid: str, timeout: int = TIMEOUT) -> Player:
    """拉取并解析一个 UID 的展柜数据。"""
    uid = str(uid).strip()
    if not uid.isdigit():
        raise MihomoError(f'UID 不合法：{uid!r}')

    url = API.format(uid=uid)
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode('utf-8', 'ignore')
    except urllib.error.HTTPError as e:
        raise MihomoError(f'接口返回 HTTP {e.code}') from e
    except urllib.error.URLError as e:
        raise MihomoError(f'网络错误：{e.reason}') from e

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        raise MihomoError('接口返回的不是 JSON') from e

    p = data.get('player') or {}
    if not p.get('uid'):
        raise MihomoError('该 UID 没有公开展柜数据（可能未开放展示或 UID 有误）')

    si = p.get('space_info') or {}
    md = si.get('memory_data') or {}
    stats = {
        'avatar_count': si.get('avatar_count'),
        'light_cone_count': si.get('light_cone_count'),
        'relic_count': si.get('relic_count'),
        'achievement_count': si.get('achievement_count'),
        'book_count': si.get('book_count'),
        'music_count': si.get('music_count'),
        'universe_level': si.get('universe_level'),
        'chaos_level': md.get('level'),
        'chaos_star': md.get('chaos_star_count'),
    }
    av = p.get('avatar') or {}

    chars = [_parse_character(c) for c in (data.get('characters') or [])]

    return Player(
        uid=str(p.get('uid')),
        nickname=p.get('nickname') or '',
        level=int(p.get('level') or 0),
        world_level=int(p.get('world_level') or 0),
        signature=p.get('signature') or '',
        avatar_id=str(av.get('id') or ''),
        avatar_name=av.get('name') or '',
        stats=stats,
        characters=chars,
    )


def format_artifact(arti: Artifact) -> str:
    """把一件遗器格式化成一行文字（调试用）。"""
    main_meta = ATTR_MAP.get(arti.main_key) or {}
    parts = []
    for s in arti.subs:
        meta = ATTR_MAP.get(s.key) or {}
        if meta.get('percent', True):
            parts.append(f'{meta.get("title", s.key)}{s.value:.1f}%')
        else:
            parts.append(f'{meta.get("title", s.key)}{s.value:.0f}')
    return (
        f'[{arti.pos}] {arti.name} Lv{arti.level} '
        f'主:{main_meta.get("title", arti.main_key)}{arti.main_value:.1f} '
        f'副:{" | ".join(parts)}'
    )
