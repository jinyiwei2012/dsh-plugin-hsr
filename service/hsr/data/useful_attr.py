# -*- coding: utf-8 -*-
"""星铁遗器词条权重表。

自动生成，请勿手工编辑。来源：
  miao-plugin/resources/meta-sr/artifact/artis-mark.js
  https://github.com/yoimiya-kokomi/miao-plugin  (MIT)

权重含义：0 = 无用，50 = 次要，75 = 有用，100 = 核心。

字段说明：
  hp      生命值 / 生命%
  atk     攻击力 / 攻击%
  def     防御力 / 防御%
  speed   速度
  cpct    暴击率
  cdmg    暴击伤害
  stance  击破特攻
  heal    治疗量加成
  recharge 能量恢复效率
  effPct  效果命中
  effDef  效果抵抗
  dmg     属性伤害加成
"""

from __future__ import annotations

USEFUL_ATTR: dict[str, dict[str, int]] = {
    "万敌": {"hp": 100, "atk": 0, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 0, "dmg": 100},
    "三月七": {"hp": 50, "atk": 0, "def": 100, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 0, "heal": 0, "recharge": 100, "effPct": 50, "effDef": 50, "dmg": 0},
    "三月七·巡猎": {"hp": 0, "atk": 100, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 0, "effPct": 0, "effDef": 0, "dmg": 100},
    "不死途": {"hp": 0, "atk": 100, "def": 0, "speed": 50, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 0, "effPct": 0, "effDef": 0, "dmg": 100},
    "丹恒": {"hp": 0, "atk": 75, "def": 0, "speed": 75, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "丹恒•腾荒": {"hp": 0, "atk": 100, "def": 0, "speed": 100, "cpct": 50, "cdmg": 50, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 0, "dmg": 50},
    "丹恒•饮月": {"hp": 0, "atk": 75, "def": 0, "speed": 50, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "乱破": {"hp": 30, "atk": 100, "def": 30, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 100, "heal": 0, "recharge": 0, "effPct": 0, "effDef": 30, "dmg": 0},
    "云璃": {"hp": 0, "atk": 75, "def": 0, "speed": 0, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 0, "dmg": 100},
    "佩拉": {"hp": 75, "atk": 0, "def": 75, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 0, "heal": 0, "recharge": 100, "effPct": 100, "effDef": 50, "dmg": 0},
    "停云": {"hp": 50, "atk": 100, "def": 0, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 0, "dmg": 0},
    "克拉拉": {"hp": 0, "atk": 75, "def": 0, "speed": 75, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "刃": {"hp": 100, "atk": 50, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "刃Pro": {"hp": 100, "atk": 0, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "刻律德菈": {"hp": 0, "atk": 100, "def": 0, "speed": 100, "cpct": 0, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 0, "dmg": 100},
    "加拉赫": {"hp": 75, "atk": 0, "def": 75, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 100, "heal": 100, "recharge": 75, "effPct": 0, "effDef": 50, "dmg": 0},
    "千冶•刃": {"hp": 100, "atk": 0, "def": 0, "speed": 50, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 50},
    "卡芙卡": {"hp": 0, "atk": 100, "def": 0, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 50, "heal": 0, "recharge": 50, "effPct": 75, "effDef": 0, "dmg": 100},
    "卡芙卡Pro": {"hp": 0, "atk": 100, "def": 0, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 50, "heal": 0, "recharge": 50, "effPct": 75, "effDef": 0, "dmg": 100},
    "卢卡": {"hp": 0, "atk": 100, "def": 0, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 75, "heal": 0, "recharge": 50, "effPct": 75, "effDef": 0, "dmg": 100},
    "吉尔伽美什": {"hp": 0, "atk": 100, "def": 0, "speed": 0, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 0, "effPct": 0, "effDef": 0, "dmg": 100},
    "大丽花": {"hp": 20, "atk": 100, "def": 20, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 100, "heal": 0, "recharge": 30, "effPct": 0, "effDef": 30, "dmg": 0},
    "大黑塔": {"hp": 0, "atk": 75, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 0, "effPct": 0, "effDef": 0, "dmg": 100},
    "姬子": {"hp": 0, "atk": 75, "def": 0, "speed": 75, "cpct": 100, "cdmg": 100, "stance": 50, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "姬子•启行": {"hp": 0, "atk": 100, "def": 0, "speed": 0, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "娜塔莎": {"hp": 100, "atk": 0, "def": 50, "speed": 75, "cpct": 0, "cdmg": 0, "stance": 0, "heal": 100, "recharge": 75, "effPct": 0, "effDef": 50, "dmg": 0},
    "寒鸦": {"hp": 75, "atk": 0, "def": 75, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 50, "dmg": 0},
    "布洛妮娅": {"hp": 75, "atk": 0, "def": 75, "speed": 100, "cpct": 0, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 50, "dmg": 0},
    "希儿": {"hp": 0, "atk": 75, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "希儿Pro": {"hp": 0, "atk": 75, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "希露瓦": {"hp": 0, "atk": 75, "def": 0, "speed": 75, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "彦卿": {"hp": 0, "atk": 75, "def": 0, "speed": 75, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 75, "effPct": 0, "effDef": 0, "dmg": 100},
    "忘归人": {"hp": 50, "atk": 0, "def": 50, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 100, "heal": 0, "recharge": 100, "effPct": 100, "effDef": 0, "dmg": 0},
    "托帕&账账": {"hp": 0, "atk": 75, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "昔涟": {"hp": 100, "atk": 0, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "星·同谐": {"hp": 75, "atk": 0, "def": 75, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 100, "heal": 0, "recharge": 75, "effPct": 0, "effDef": 0, "dmg": 0},
    "星·存护": {"hp": 50, "atk": 0, "def": 100, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 0, "heal": 0, "recharge": 0, "effPct": 100, "effDef": 50, "dmg": 0},
    "星·欢愉": {"hp": 0, "atk": 100, "def": 0, "speed": 100, "cpct": 75, "cdmg": 75, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 0, "dmg": 0},
    "星·毁灭": {"hp": 0, "atk": 75, "def": 0, "speed": 75, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "星·记忆": {"hp": 0, "atk": 100, "def": 0, "speed": 100, "cpct": 0, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 0},
    "星期日": {"hp": 75, "atk": 0, "def": 75, "speed": 100, "cpct": 0, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 50, "dmg": 0},
    "景元": {"hp": 0, "atk": 75, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "杰帕德": {"hp": 50, "atk": 0, "def": 100, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 0, "heal": 0, "recharge": 100, "effPct": 50, "effDef": 50, "dmg": 0},
    "桂乃芬": {"hp": 0, "atk": 100, "def": 0, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 50, "heal": 0, "recharge": 50, "effPct": 75, "effDef": 0, "dmg": 100},
    "桑博": {"hp": 0, "atk": 75, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 100, "effDef": 0, "dmg": 100},
    "椒丘": {"hp": 75, "atk": 50, "def": 75, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 0, "heal": 0, "recharge": 0, "effPct": 100, "effDef": 50, "dmg": 0},
    "波提欧": {"hp": 50, "atk": 50, "def": 50, "speed": 100, "cpct": 50, "cdmg": 50, "stance": 100, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 50},
    "流萤": {"hp": 30, "atk": 100, "def": 30, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 100, "heal": 0, "recharge": 0, "effPct": 0, "effDef": 30, "dmg": 0},
    "流萤Pro": {"hp": 10, "atk": 100, "def": 0, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 100, "heal": 0, "recharge": 0, "effPct": 0, "effDef": 30, "dmg": 0},
    "海瑟音": {"hp": 0, "atk": 100, "def": 0, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 0, "heal": 0, "recharge": 0, "effPct": 100, "effDef": 0, "dmg": 100},
    "火花": {"hp": 0, "atk": 75, "def": 0, "speed": 50, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 0},
    "灵砂": {"hp": 0, "atk": 75, "def": 0, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 100, "heal": 100, "recharge": 100, "effPct": 0, "effDef": 0, "dmg": 0},
    "爻光": {"hp": 75, "atk": 0, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 0, "dmg": 0},
    "玲可": {"hp": 100, "atk": 0, "def": 50, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 0, "heal": 100, "recharge": 75, "effPct": 0, "effDef": 50, "dmg": 0},
    "瓦尔特": {"hp": 0, "atk": 75, "def": 0, "speed": 75, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 100, "effDef": 0, "dmg": 100},
    "瓦尔特Pro": {"hp": 0, "atk": 75, "def": 0, "speed": 75, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 100, "effDef": 0, "dmg": 100},
    "白厄": {"hp": 0, "atk": 75, "def": 0, "speed": 0, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 0, "effPct": 0, "effDef": 0, "dmg": 100},
    "白露": {"hp": 100, "atk": 0, "def": 50, "speed": 75, "cpct": 0, "cdmg": 0, "stance": 0, "heal": 100, "recharge": 100, "effPct": 0, "effDef": 50, "dmg": 0},
    "真珠": {"hp": 0, "atk": 0, "def": 100, "speed": 75, "cpct": 0, "cdmg": 0, "stance": 0, "heal": 100, "recharge": 100, "effPct": 0, "effDef": 100, "dmg": 0},
    "真理医生": {"hp": 0, "atk": 75, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "知更鸟": {"hp": 75, "atk": 100, "def": 75, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 50, "dmg": 0},
    "知更鸟•晴歌": {"hp": 100, "atk": 0, "def": 0, "speed": 100, "cpct": 50, "cdmg": 50, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 0, "dmg": 0},
    "砂金": {"hp": 0, "atk": 0, "def": 100, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 75, "effPct": 0, "effDef": 50, "dmg": 100},
    "砂金•戏浪": {"hp": 100, "atk": 0, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 0, "effPct": 0, "effDef": 0, "dmg": 0},
    "穹·同谐": {"hp": 75, "atk": 0, "def": 75, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 100, "heal": 0, "recharge": 75, "effPct": 0, "effDef": 0, "dmg": 0},
    "穹·存护": {"hp": 50, "atk": 0, "def": 100, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 0, "heal": 0, "recharge": 0, "effPct": 100, "effDef": 50, "dmg": 0},
    "穹·欢愉": {"hp": 0, "atk": 100, "def": 0, "speed": 100, "cpct": 75, "cdmg": 75, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 0, "dmg": 0},
    "穹·毁灭": {"hp": 0, "atk": 75, "def": 0, "speed": 75, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "穹·记忆": {"hp": 0, "atk": 100, "def": 0, "speed": 100, "cpct": 0, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 0},
    "符玄": {"hp": 100, "atk": 0, "def": 50, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 50, "dmg": 100},
    "米沙": {"hp": 0, "atk": 75, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 75, "effPct": 0, "effDef": 0, "dmg": 100},
    "素裳": {"hp": 0, "atk": 75, "def": 0, "speed": 75, "cpct": 100, "cdmg": 100, "stance": 50, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "绯英": {"hp": 0, "atk": 100, "def": 0, "speed": 50, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 0, "dmg": 100},
    "缇宝": {"hp": 100, "atk": 0, "def": 0, "speed": 0, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 0, "dmg": 100},
    "罗刹": {"hp": 0, "atk": 100, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 100, "recharge": 100, "effPct": 0, "effDef": 50, "dmg": 100},
    "翡翠": {"hp": 0, "atk": 75, "def": 0, "speed": 75, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "艾丝妲": {"hp": 0, "atk": 75, "def": 0, "speed": 100, "cpct": 75, "cdmg": 75, "stance": 100, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 0, "dmg": 100},
    "花火": {"hp": 75, "atk": 0, "def": 75, "speed": 100, "cpct": 0, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 50, "dmg": 0},
    "花火Pro": {"hp": 75, "atk": 0, "def": 75, "speed": 100, "cpct": 0, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 50, "dmg": 0},
    "藿藿": {"hp": 100, "atk": 0, "def": 50, "speed": 75, "cpct": 0, "cdmg": 0, "stance": 0, "heal": 100, "recharge": 100, "effPct": 0, "effDef": 50, "dmg": 0},
    "藿藿Pro": {"hp": 100, "atk": 0, "def": 50, "speed": 75, "cpct": 0, "cdmg": 0, "stance": 0, "heal": 100, "recharge": 100, "effPct": 0, "effDef": 50, "dmg": 0},
    "虎克": {"hp": 0, "atk": 75, "def": 0, "speed": 75, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "貊泽": {"hp": 0, "atk": 75, "def": 0, "speed": 50, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 0, "dmg": 100},
    "赛飞儿": {"hp": 0, "atk": 75, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 100, "effPct": 75, "effDef": 0, "dmg": 100},
    "远坂凛": {"hp": 0, "atk": 100, "def": 0, "speed": 75, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 0, "dmg": 100},
    "遐蝶": {"hp": 100, "atk": 0, "def": 0, "speed": 0, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 0, "effPct": 0, "effDef": 30, "dmg": 100},
    "那刻夏": {"hp": 0, "atk": 75, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 0, "dmg": 100},
    "银枝": {"hp": 0, "atk": 75, "def": 0, "speed": 75, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 75, "effPct": 0, "effDef": 0, "dmg": 100},
    "银狼": {"hp": 0, "atk": 75, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 75, "effPct": 100, "effDef": 0, "dmg": 100},
    "银狼LV.999": {"hp": 10, "atk": 0, "def": 10, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 0, "effPct": 0, "effDef": 0, "dmg": 0},
    "银狼Pro": {"hp": 0, "atk": 75, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 75, "effPct": 100, "effDef": 0, "dmg": 100},
    "镜流": {"hp": 0, "atk": 75, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "镜流Pro": {"hp": 100, "atk": 0, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "长夜月": {"hp": 100, "atk": 0, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "阮•梅": {"hp": 75, "atk": 0, "def": 75, "speed": 100, "cpct": 0, "cdmg": 0, "stance": 100, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 50, "dmg": 0},
    "阿兰": {"hp": 0, "atk": 75, "def": 0, "speed": 75, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "阿格莱雅": {"hp": 0, "atk": 75, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 0, "effPct": 0, "effDef": 0, "dmg": 100},
    "雪衣": {"hp": 0, "atk": 75, "def": 0, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 100, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "青雀": {"hp": 0, "atk": 75, "def": 0, "speed": 75, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "风堇": {"hp": 100, "atk": 0, "def": 0, "speed": 100, "cpct": 0, "cdmg": 75, "stance": 0, "heal": 100, "recharge": 100, "effPct": 0, "effDef": 50, "dmg": 0},
    "飞霄": {"hp": 0, "atk": 75, "def": 0, "speed": 75, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 0, "dmg": 100},
    "驭空": {"hp": 50, "atk": 75, "def": 50, "speed": 100, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 100, "effPct": 0, "effDef": 50, "dmg": 100},
    "黄泉": {"hp": 0, "atk": 100, "def": 0, "speed": 75, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 0, "effPct": 0, "effDef": 0, "dmg": 100},
    "黑塔": {"hp": 0, "atk": 75, "def": 0, "speed": 75, "cpct": 100, "cdmg": 100, "stance": 0, "heal": 0, "recharge": 50, "effPct": 0, "effDef": 0, "dmg": 100},
    "黑天鹅": {"hp": 0, "atk": 100, "def": 0, "speed": 75, "cpct": 0, "cdmg": 0, "stance": 0, "heal": 0, "recharge": 50, "effPct": 100, "effDef": 0, "dmg": 100},
    "黑天鹅Pro": {"hp": 0, "atk": 100, "def": 0, "speed": 75, "cpct": 0, "cdmg": 0, "stance": 0, "heal": 0, "recharge": 50, "effPct": 100, "effDef": 0, "dmg": 100},
}


def get_useful_attr(char_name: str) -> dict[str, int]:
    """取角色词条权重；未收录返回空 dict。"""
    return USEFUL_ATTR.get(char_name) or {}
