# -*- coding: utf-8 -*-
"""星铁遗器评分引擎。

移植自 miao-plugin（MIT）
    models/artis/ArtisMark.js
    models/artis/ArtisMarkCfg.js
    https://github.com/yoimiya-kokomi/miao-plugin

算法要点
--------
每个词条的权重来自 ``USEFUL_ATTR``（0~100）。权重先折算成 ``mark``：

    普通词条:   mark = weight / value
    小词条:     mark = weight / 大词条value / (大词条基础值 + 修正) * 100

其中 ``value`` 是单次档位最大值。于是 ``mark * 实际数值`` 在「满档」时正好
等于权重本身 —— 这就是评分可跨角色比较的原因。

单件得分::

    ret = Σ(mark_i * value_i)                 # 副词条
        + mark_main * main_value / 4          # 主词条按 1/4 折算
    score = min(ret * (1 + fixPct) / 2 / pMax * 66, 70)

``pMax`` 是该部位在当前主词条下的理论满档分，``fixPct`` 修正主词条与角色
需求的匹配度（主词条越契合，系数越高）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..data.attr_meta import (
    ATTR_MAP,
    BASE_MAP,
    FIXED_MAIN_POS,
    MAIN_ATTR,
    POS_NAMES,
    SUB_ATTR,
    mark_class,
)
from ..data.useful_attr import get_useful_attr

# 主词条满分系数（与 miao 一致）
MAIN_DIVISOR = 4
# 小攻击的基础值修正
ATK_PLUS_BONUS = 520
# 未提供角色基础属性时的兜底
DEFAULT_BASE_ATTR = {'hp': 14000, 'atk': 230, 'def': 700}
# 星铁默认权重（角色未收录时）
DEFAULT_WEIGHT = {'atk': 75, 'cpct': 100, 'cdmg': 100, 'dmg': 100, 'speed': 100}


@dataclass
class SubAffix:
    """一条副词条。"""

    key: str
    value: float
    count: int = 1
    name: str = ''


@dataclass
class Artifact:
    """一件遗器。"""

    pos: int
    name: str = ''
    set_name: str = ''
    level: int = 15
    rarity: int = 5
    main_key: str = ''
    main_value: float = 0.0
    main_name: str = ''
    subs: list[SubAffix] = field(default_factory=list)
    # 图标（相对资源库路径）
    icon: str = ''


@dataclass
class CharCfg:
    """一个角色的评分配置。"""

    char_name: str
    title: str
    attrs: dict[str, dict]
    pos_max: dict[Any, float]
    weight: dict[str, int]


def build_attrs(weight: dict[str, int], base_attr: dict[str, float] | None = None) -> dict[str, dict]:
    """把权重表展开成带 mark / fixWeight 的词条字典。"""
    base_attr = base_attr or DEFAULT_BASE_ATTR
    out: dict[str, dict] = {}
    for key, meta in ATTR_MAP.items():
        parent = BASE_MAP.get(key, '')
        w = weight.get(parent or key)
        if not w:
            continue
        rec = {
            'title': meta['title'],
            'value': meta['value'],
            'percent': meta['percent'],
            'weight': w,
            'fixWeight': w,
        }
        if not parent:
            rec['mark'] = w / meta['value']
        else:
            plus = ATK_PLUS_BONUS if parent == 'atk' else 0
            denom = (base_attr.get(parent) or DEFAULT_BASE_ATTR[parent]) + plus
            parent_value = ATTR_MAP[parent]['value']
            rec['mark'] = w / parent_value / denom * 100
            rec['fixWeight'] = w * meta['value'] / parent_value / denom * 100
        out[key] = rec
    return out


def _max_attrs(attrs: dict[str, dict], pool: list[str], limit: int = 1, ban: str = '') -> list[str]:
    """按 fixWeight 从高到低取前 limit 个可用词条。"""
    cand = [(a, attrs[a]['fixWeight']) for a in pool if a != ban and a in attrs]
    cand.sort(key=lambda x: -x[1])
    return [a for a, _ in cand][:limit]


def _max_mark(attrs: dict[str, dict]) -> dict[Any, float]:
    """每个部位的裸分上限（按该部位最优主词条）。"""
    ret: dict[Any, float] = {}
    for pos in range(1, 7):
        total = 0.0
        m_mark = 0.0
        if pos == 1:
            main = 'hpPlus'
        elif pos == 2:
            main = 'atkPlus'
        else:
            cand = _max_attrs(attrs, MAIN_ATTR[pos])
            if cand:
                main = cand[0]
                m_mark = attrs[main]['fixWeight']
                total += m_mark * 2
            else:
                main = MAIN_ATTR[pos][0]
        subs = _max_attrs(attrs, SUB_ATTR, 4, main)
        for i, a in enumerate(subs):
            total += attrs[a]['fixWeight'] * (6 if i == 0 else 1)
        ret[pos] = total
        ret[f'm{pos}'] = m_mark
    return ret


def _main_max_mark(attrs: dict[str, dict], main_key: str) -> float:
    """指定主词条下该部位的裸分上限（主词条属性可作为副词条出现）。"""
    if main_key not in attrs:
        return 0.0
    total = attrs[main_key]['fixWeight'] * 2
    subs = _max_attrs(attrs, SUB_ATTR, 4, main_key)
    for i, a in enumerate(subs):
        total += attrs[a]['fixWeight'] * (6 if i == 0 else 1)
    return total


def make_char_cfg(char_name: str, base_attr: dict[str, float] | None = None) -> CharCfg:
    """构造角色评分配置。"""
    weight = get_useful_attr(char_name) or dict(DEFAULT_WEIGHT)
    attrs = build_attrs(weight, base_attr)
    pos_max = _max_mark(attrs)
    has_table = bool(get_useful_attr(char_name))
    title = f'{char_name}-' + ('专属' if has_table else '通用')
    return CharCfg(char_name=char_name, title=title, attrs=attrs, pos_max=pos_max, weight=weight)


def score_artifact(cfg: CharCfg, arti: Artifact) -> float:
    """给单件遗器打分（0~70）。"""
    pos = arti.pos
    key = arti.main_key
    if not key:
        return 0.0

    fix_pct = 1.0
    p_max = cfg.pos_max.get(pos, 0.0)
    ret = 0.0

    if pos >= 3:
        if key != 'recharge':
            m_max = cfg.pos_max.get(f'm{pos}', 0.0)
            w = (cfg.attrs.get(key) or {}).get('weight', 0)
            fix_pct = max(0.0, min(1.0, w / m_max)) if m_max else 1.0
        ret += (cfg.attrs.get(key) or {}).get('mark', 0) * arti.main_value / MAIN_DIVISOR
        p_max = max(p_max, _main_max_mark(cfg.attrs, key))

    for sub in arti.subs:
        ret += (cfg.attrs.get(sub.key) or {}).get('mark', 0) * sub.value

    if p_max <= 0:
        return 0.0
    return min(ret * (1 + fix_pct) / 2 / p_max * 66, 70)


@dataclass
class ArtifactScore:
    """单件评分结果。"""

    pos: int
    pos_name: str
    name: str
    set_name: str
    score: float
    grade: str
    p_max: float
    main_title: str
    main_value: float
    main_weight: int
    sub_rows: list[dict]
    icon: str = ''
    level: int = 0
    main_mark_display: float = 0.0


@dataclass
class ScoreReport:
    """整套评分结果。"""

    char_name: str
    title: str
    total: float
    average: float
    grade: str
    pieces: list[ArtifactScore]
    weight: dict[str, int]


def score_set(
    char_name: str,
    artifacts: list[Artifact],
    base_attr: dict[str, float] | None = None,
) -> ScoreReport:
    """给一整套（6 件）遗器打分。"""
    cfg = make_char_cfg(char_name, base_attr)
    pieces: list[ArtifactScore] = []
    total = 0.0

    for arti in artifacts:
        s = score_artifact(cfg, arti)
        total += s
        main_meta = ATTR_MAP.get(arti.main_key) or {}
        sub_rows = []
        for sub in arti.subs:
            meta = ATTR_MAP.get(sub.key) or {}
            ent = cfg.attrs.get(sub.key) or {}
            weight = ent.get('weight', 0)
            # 与 miao 展示口径一致：46.6 / 6 / 100 * (mark * 数值)
            contrib = ent.get('mark', 0) * sub.value
            sub_rows.append({
                'key': sub.key,
                'title': meta.get('title') or sub.name or sub.key,
                'value': sub.value,
                'percent': meta.get('percent', True),
                'weight': weight,
                'count': sub.count,
                'useless': weight == 0,
                'mark_display': 46.6 / 6 / 100 * contrib,
            })
        sub_rows.sort(key=lambda r: -r['weight'])
        # 主词条的展示分（与 miao 一致：主词条按 1/4 折算）
        main_mark = 0.0
        if arti.pos >= 3:
            ent = cfg.attrs.get(arti.main_key) or {}
            main_mark = 46.6 / 6 / 100 * ent.get('mark', 0) * arti.main_value / 4

        pieces.append(ArtifactScore(
            pos=arti.pos,
            pos_name=POS_NAMES.get(arti.pos, str(arti.pos)),
            name=arti.name,
            set_name=arti.set_name,
            score=s,
            grade=mark_class(s),
            p_max=cfg.pos_max.get(arti.pos, 0.0),
            main_title=main_meta.get('title') or arti.main_name or arti.main_key,
            main_value=arti.main_value,
            main_weight=(cfg.attrs.get(arti.main_key) or {}).get('weight', 0),
            sub_rows=sub_rows,
            icon=arti.icon,
            level=arti.level,
            main_mark_display=main_mark,
        ))

    pieces.sort(key=lambda p: p.pos)
    # 星铁固定按 6 件折算（缺件即扣分），与 miao 口径一致
    avg = total / 6
    return ScoreReport(
        char_name=char_name,
        title=cfg.title,
        total=total,
        average=avg,
        grade=mark_class(avg),
        pieces=pieces,
        weight=cfg.weight,
    )


def improvement_hint(report: ScoreReport) -> list[str]:
    """根据评分结果给出可读的提升建议。

    顺序：无效词条 → 低权重词条 → 主词条错配 → 缺件。
    无效词条（权重 0）是最确定的收益，优先列出。
    """
    hints: list[str] = []

    useless_hits: list[str] = []
    low_hits: list[str] = []
    for p in sorted(report.pieces, key=lambda x: x.pos):
        useless = [r['title'] for r in p.sub_rows if r['useless']]
        low = [r['title'] for r in p.sub_rows if 0 < r['weight'] < 75]
        if useless:
            useless_hits.append(
                f'{p.pos_name}（{p.name}，{p.score:.1f} 分 / {p.grade}）'
                f'无效词条：{"、".join(useless)}'
            )
        elif low:
            low_hits.append(
                f'{p.pos_name}（{p.name}，{p.score:.1f} 分 / {p.grade}）'
                f'低权重：{"、".join(low)}'
            )

    if useless_hits:
        hints.append('【优先替换】以下遗器含对该角色完全无用的词条：')
        hints.extend('  · ' + h for h in useless_hits)
    if low_hits:
        hints.append('【次要】以下遗器词条有用但权重不高：')
        hints.extend('  · ' + h for h in low_hits)

    # 主词条错配（头部/手部主词条固定，不参与）
    for p in report.pieces:
        if p.main_weight == 0 and p.pos not in FIXED_MAIN_POS:
            hints.append(
                f'【错配】{p.pos_name} 主词条「{p.main_title}」对该角色权重为 0，'
                '应更换主词条'
            )

    # 缺件
    have = {p.pos for p in report.pieces}
    missing = [POS_NAMES[i] for i in range(1, 7) if i not in have]
    if missing:
        hints.append(
            '【缺件】' + '、'.join(missing)
            + ' 未装备（总分按 6 件折算，缺件直接拉低）'
        )

    return hints
