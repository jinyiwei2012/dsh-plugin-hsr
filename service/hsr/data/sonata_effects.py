# -*- coding: utf-8 -*-
"""星铁遗器套装数值加成（仅可静态结算的部分）。

自动生成，请勿手工编辑。来源：
  miao-plugin/resources/meta-sr/artifact/calc.js
  https://github.com/yoimiya-kokomi/miao-plugin  (MIT)

只收录「常驻无条件」的数值型效果；条件型效果（需命中/入场等触发）
不参与面板计算，因此不在本表中。
"""

from __future__ import annotations

SONATA_EFFECTS: dict[str, dict[str, dict[str, float]]] = {
    "云无留迹的过客": {"two": {"heal": 10.0}},
    "再创天地的救世主": {"two": {"cpct": 8.0}},
    "净庭教宗的圣骑士": {"two": {"defPct": 15.0}},
    "凯歌祝捷的英豪": {"two": {"atkPct": 12.0}},
    "叩问天工的名冶": {"two": {"hpPct": 12.0}},
    "哀歌覆国的诗人": {"two": {"quantum": 10.0}, "four": {"speedPct": -8.0}},
    "宝命长存的莳者": {"two": {"hpPct": 12.0}},
    "密林卧雪的猎人": {"two": {"ice": 10.0}},
    "幽锁深牢的系囚": {"two": {"atkPct": 12.0}},
    "应天涉远的卜者": {"two": {"speedPct": 6.0}},
    "恶海逐波的船长": {"two": {"cdmg": 16.0}},
    "戏梦点星的伶人": {"two": {"speedPct": 6.0}},
    "星体差分机": {"two": {"cdmg": 16.0}},
    "星如我见的领航员": {"two": {"atkPct": 12.0}},
    "晨昏交界的翔鹰": {"two": {"wind": 10.0}},
    "机心戏梦的钟表匠": {"two": {"stance": 16.0}},
    "死水深潜的先驱": {"four": {"cpct": 4.0}},
    "沉陆海域露莎卡": {"two": {"recharge": 5.0}},
    "流星追迹的怪盗": {"two": {"stance": 16.0}, "four": {"stance": 16.0}},
    "激奏雷电的乐队": {"two": {"elec": 10.0}},
    "烈阳惊雷的女武神": {"two": {"speedPct": 6.0}},
    "熔岩锻铸的火匠": {"two": {"fire": 10.0}},
    "生命的翁瓦克": {"two": {"recharge": 5.0}},
    "盗匪荒漠的废土客": {"two": {"imaginary": 10.0}},
    "繁星璀璨的天才": {"two": {"quantum": 10.0}},
    "自匿星芒的隐士": {"two": {"shield": 10.0}},
    "荡除蠹灾的铁骑": {"two": {"stance": 16.0}},
    "街头出身的拳王": {"two": {"phy": 10.0}},
    "识海迷坠的学者": {"two": {"cpct": 8.0}},
    "贪噬禁果的异端": {"two": {"cpct": 16.0}},
    "重循苦旅的司铎": {"two": {"speedPct": 6.0}},
    "野穗伴行的快枪手": {"two": {"atkPct": 12.0}, "four": {"speedPct": 6.0}},
    "闪耀功勋的魔法少女": {"two": {"cdmg": 16.0}, "four": {"ignore": 10.0}},
    "风举云飞的勇烈": {"two": {"atkPct": 12.0}, "four": {"cpct": 6.0}},
    "骇域漫游的信使": {"two": {"speedPct": 6.0}},
}


def get_sonata_effect(set_name: str, count: int) -> dict[str, float]:
    """返回该套装在 count 件时生效的数值加成。"""
    entry = SONATA_EFFECTS.get(set_name) or {}
    out: dict[str, float] = {}
    if count >= 2:
        out.update(entry.get("two") or {})
    if count >= 4:
        out.update(entry.get("four") or {})
    return out
