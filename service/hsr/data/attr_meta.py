# -*- coding: utf-8 -*-
"""星铁遗器词条定义。

来源：miao-plugin/resources/meta-sr/artifact/meta.js  (MIT)
    https://github.com/yoimiya-kokomi/miao-plugin

`value` 为该词条**单次强化档位的最大值**，是评分归一化的基准。
`mark` 由权重除以 value 得到，见 core/artifact.py。
"""

from __future__ import annotations

# 词条定义：value = 单次档位最大值
ATTR_MAP: dict[str, dict] = {
    'atk':      {'title': '大攻击',   'value': 4.32,     'percent': True},
    'atkPlus':  {'title': '小攻击',   'value': 127 / 6,  'percent': False},
    'def':      {'title': '大防御',   'value': 5.4,      'percent': True},
    'defPlus':  {'title': '小防御',   'value': 127 / 6,  'percent': False},
    'hp':       {'title': '大生命',   'value': 4.32,     'percent': True},
    'hpPlus':   {'title': '小生命',   'value': 254 / 6,  'percent': False},
    'speed':    {'title': '速度',     'value': 2.6,      'percent': False},
    'cpct':     {'title': '暴击率',   'value': 3.24,     'percent': True},
    'cdmg':     {'title': '暴击伤害', 'value': 6.48,     'percent': True},
    'recharge': {'title': '充能效率', 'value': 3.11,     'percent': True},
    'dmg':      {'title': '伤害加成', 'value': 6.22,     'percent': True},
    'heal':     {'title': '治疗加成', 'value': 5.53,     'percent': True},
    'stance':   {'title': '击破特攻', 'value': 6.48,     'percent': True},
    'effPct':   {'title': '效果命中', 'value': 4.32,     'percent': True},
    'effDef':   {'title': '效果抵抗', 'value': 4.32,     'percent': True},
}

# 小词条 -> 对应大词条
BASE_MAP: dict[str, str] = {
    'hpPlus': 'hp',
    'atkPlus': 'atk',
    'defPlus': 'def',
}

# 各部位可选主词条（1=头 2=手 3=躯干 4=脚 5=位面球 6=连结绳）
MAIN_ATTR: dict[int, list[str]] = {
    1: [],
    2: [],
    3: ['atk', 'def', 'hp', 'cpct', 'cdmg', 'heal', 'effPct'],
    4: ['atk', 'def', 'hp', 'speed'],
    5: ['atk', 'def', 'hp', 'dmg'],
    6: ['atk', 'def', 'hp', 'recharge', 'stance'],
}

# 可出现的副词条池（不含 dmg / heal，两者只能做主词条）
SUB_ATTR: list[str] = [
    'atk', 'atkPlus', 'def', 'defPlus', 'hp', 'hpPlus',
    'speed', 'cpct', 'cdmg', 'effPct', 'effDef', 'stance',
]

# 部位名
POS_NAMES: dict[int, str] = {
    1: '头部',
    2: '手部',
    3: '躯干',
    4: '脚部',
    5: '位面球',
    6: '连结绳',
}

# 属性中文名 -> 主词条 field 前缀（mihomo/HoYo API 用）
# 注意：雷是 thunder_dmg，不是 lightning_dmg
ELEMENT_FIELD: dict[str, str] = {
    '物理': 'physical_dmg',
    '火': 'fire_dmg',
    '冰': 'ice_dmg',
    '雷': 'thunder_dmg',
    '风': 'wind_dmg',
    '量子': 'quantum_dmg',
    '虚数': 'imaginary_dmg',
}

# 元素伤害 field 集合（反向查表用），兼容 lightning_dmg 写法
DMG_FIELDS: set[str] = set(ELEMENT_FIELD.values()) | {'lightning_dmg'}

# 主词条固定的部位（头部=小生命、手部=小攻击），不能更换
FIXED_MAIN_POS: frozenset[int] = frozenset({1, 2})

# mihomo/游戏 API 的 affix type -> 本模块词条 key
AFFIX_TYPE_MAP: dict[str, str] = {
    'HPDelta': 'hpPlus',
    'HPAddedRatio': 'hp',
    'AttackDelta': 'atkPlus',
    'AttackAddedRatio': 'atk',
    'DefenceDelta': 'defPlus',
    'DefenceAddedRatio': 'def',
    'SpeedDelta': 'speed',
    'CriticalChanceBase': 'cpct',
    'CriticalDamageBase': 'cdmg',
    'StatusProbabilityBase': 'effPct',
    'StatusResistanceBase': 'effDef',
    'BreakDamageAddedRatioBase': 'stance',
    'SPRatioBase': 'recharge',
    'HealRatioBase': 'heal',
}

# 评分档位（单件与均值共用）
MARK_CLASS: list[tuple[str, float]] = [
    ('D', 7), ('C', 14), ('B', 21), ('A', 28),
    ('S', 35), ('SS', 42), ('SSS', 49), ('ACE', 56), ('MAX', 70),
]


# 元素伤害的 affix type -> field（接口两种写法都要兼容）
ELEM_TYPE_MAP: dict[str, str] = {
    'PhysicalAddedRatio': 'physical_dmg',
    'FireAddedRatio': 'fire_dmg',
    'IceAddedRatio': 'ice_dmg',
    'ThunderAddedRatio': 'thunder_dmg',
    'LightningAddedRatio': 'thunder_dmg',
    'WindAddedRatio': 'wind_dmg',
    'QuantumAddedRatio': 'quantum_dmg',
    'ImaginaryAddedRatio': 'imaginary_dmg',
}


def mark_class(value: float) -> str:
    """按分数返回评级字母。"""
    for name, limit in MARK_CLASS:
        if value < limit:
            return name
    return 'MAX'


def affix_to_key(affix_type: str, field: str = '') -> str:
    """把游戏 API 的词条类型翻成本模块 key。

    元素伤害统一返回 'dmg'，是否与角色属性匹配由调用方判断。
    """
    if affix_type in ELEM_TYPE_MAP:
        return 'dmg'
    if field in DMG_FIELDS:
        return 'dmg'
    return AFFIX_TYPE_MAP.get(affix_type, '')


def element_field_of(affix_type: str, field: str = '') -> str:
    """取元素伤害对应的 field 名（非元素伤害返回空串）。"""
    if affix_type in ELEM_TYPE_MAP:
        return ELEM_TYPE_MAP[affix_type]
    if field in DMG_FIELDS:
        return 'thunder_dmg' if field == 'lightning_dmg' else field
    return ''
