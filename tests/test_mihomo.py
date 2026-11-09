# -*- coding: utf-8 -*-
"""mihomo 数据适配测试（用内联样例，不联网）。"""

import os
import sys
import unittest

SERVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'service')
sys.path.insert(0, SERVICE)

from hsr.api.mihomo import _parse_artifact, _parse_character  # noqa: E402


CHAR_RAW = {
    'id': '1415',
    'name': '昔涟',
    'rarity': 5,
    'rank': 6,
    'level': 80,
    'path': {'name': '记忆'},
    'element': {'name': '冰'},
    'attributes': [
        {'name': '基础生命值', 'value': 2667.0},
        {'name': '基础攻击力', 'value': 922.0},
        {'name': '基础防御力', 'value': 1045.0},
        {'name': '速度', 'value': 101.0},
        {'name': '暴击率', 'value': 0.05},
        {'name': '暴击伤害', 'value': 0.5},
    ],
    'additions': [
        {'name': '基础生命值', 'value': 3134.0},
        {'name': '基础攻击力', 'value': 424.0},
        {'name': '基础防御力', 'value': 67.0},
        {'name': '速度', 'value': 78.0},
        {'name': '暴击率', 'value': 0.341},
        {'name': '暴击伤害', 'value': 1.941},
        {'name': '冰属性伤害提高', 'value': 0.388},
    ],
    'relics': [
        {
            'type': 5,
            'name': '翁法罗斯的西风尽途',
            'set_name': '永恒之地翁法罗斯',
            'level': 15,
            'rarity': 5,
            'main_affix': {
                'type': 'IceAddedRatio', 'field': 'ice_dmg',
                'name': '冰属性伤害提高', 'value': 0.3888, 'percent': True,
            },
            'sub_affix': [
                {'type': 'CriticalChanceBase', 'field': 'crit_rate',
                 'name': '暴击率', 'value': 0.0612, 'percent': True, 'count': 2},
            ],
        },
    ],
}


class TestPanelTotals(unittest.TestCase):
    """面板必须是「基础 + 加成」，不是只取加成。"""

    def setUp(self):
        self.c = _parse_character(CHAR_RAW)

    def test_hp_is_base_plus_bonus(self):
        self.assertAlmostEqual(self.c.panel['生命值'], 2667.0 + 3134.0)

    def test_speed_is_base_plus_bonus(self):
        self.assertAlmostEqual(self.c.panel['速度'], 101.0 + 78.0)

    def test_crit_is_base_plus_bonus(self):
        self.assertAlmostEqual(self.c.panel['暴击率'], 0.391, places=4)
        self.assertAlmostEqual(self.c.panel['暴击伤害'], 2.441, places=4)

    def test_elemental_damage_kept(self):
        self.assertAlmostEqual(self.c.panel['冰属性伤害提高'], 0.388)

    def test_base_attr_for_scoring(self):
        self.assertAlmostEqual(self.c.base_attr['hp'], 2667.0)
        self.assertAlmostEqual(self.c.base_attr['atk'], 922.0)
        self.assertAlmostEqual(self.c.base_attr['def'], 1045.0)


class TestArtifactParse(unittest.TestCase):
    def test_on_element_orb(self):
        raw = CHAR_RAW['relics'][0]
        a = _parse_artifact(raw, 5, '冰')
        self.assertEqual(a.main_key, 'dmg', '同属性球应计 dmg 权重')
        self.assertAlmostEqual(a.main_value, 38.88, places=2)

    def test_off_element_orb(self):
        raw = CHAR_RAW['relics'][0]
        a = _parse_artifact(raw, 5, '火')
        self.assertTrue(a.main_key.startswith('__elem__'), '异色球应标记为非 dmg')

    def test_percent_values_scaled(self):
        raw = CHAR_RAW['relics'][0]
        a = _parse_artifact(raw, 5, '冰')
        # 6.12% 应换算成 6.12，而不是 0.0612
        self.assertAlmostEqual(a.subs[0].value, 6.12, places=3)
        self.assertEqual(a.subs[0].key, 'cpct')


if __name__ == '__main__':
    unittest.main(verbosity=2)
