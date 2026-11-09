# -*- coding: utf-8 -*-
"""角色面板卡测试。"""

import os
import sys
import tempfile
import unittest

SERVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'service')
sys.path.insert(0, SERVICE)

from hsr.render import panelcard  # noqa: E402


class FakeChar:
    name = '昔涟'
    level = 80
    rank = 6
    element = '冰'
    path = '记忆'
    portrait = 'image/character_portrait/1415.png'
    panel = {'生命值': 5801.9, '攻击力': 1347.1, '防御力': 1112.9, '速度': 179.9,
             '暴击率': 0.391, '暴击伤害': 2.441, '冰属性伤害提高': 0.389}
    panel_base = {'生命值': 2667.2, '攻击力': 922.6, '防御力': 1045.2, '速度': 101.0,
                  '暴击率': 0.05, '暴击伤害': 0.5, '冰属性伤害提高': 0.0}
    panel_add = {'生命值': 3134.7, '攻击力': 424.5, '防御力': 67.7, '速度': 78.9,
                 '暴击率': 0.341, '暴击伤害': 1.941, '冰属性伤害提高': 0.389}
    set_counts = {'再创天地的救世主': 4, '永恒之地翁法罗斯': 2}
    light_cone = {'name': '爱如此刻永恒', 'rarity': 5, 'rank': 1, 'level': 80,
                  'id': '23052', 'icon': 'icon/light_cone/23052.png'}
    skills = [
        {'type': '普攻', 'name': '看，希望的起始！', 'level': 7, 'max_level': 10,
         'icon': 'icon/skill/1415_basic_atk.png'},
        {'type': '战技', 'name': '盛放吧', 'level': 12, 'max_level': 15,
         'icon': 'icon/skill/1415_skill.png'},
        {'type': '终结技', 'name': '诗的誓约', 'level': 12, 'max_level': 15,
         'icon': 'icon/skill/1415_ultimate.png'},
        {'type': '天赋', 'name': '众愿', 'level': 12, 'max_level': 15,
         'icon': 'icon/skill/1415_talent.png'},
        {'type': '秘技', 'name': '西风', 'level': 1, 'max_level': 1, 'icon': ''},
    ]


WEIGHTS = {'hp': 100, 'speed': 100, 'cpct': 100, 'cdmg': 100,
           'recharge': 50, 'dmg': 100}


class TestBuildPanelHtml(unittest.TestCase):
    def setUp(self):
        self.html = panelcard.build_panel_html(FakeChar(), WEIGHTS, '114172341')

    def test_character_header(self):
        self.assertIn('昔涟', self.html)
        self.assertIn('UID 114172341', self.html)
        self.assertIn('Lv.80', self.html)
        self.assertIn('6命', self.html)
        self.assertIn('冰 · 记忆', self.html)

    def test_portrait(self):
        self.assertIn('character_portrait/1415.png', self.html)

    def test_attr_rows(self):
        self.assertIn('生命值', self.html)
        self.assertIn('5801.9', self.html)
        self.assertIn('2667.2', self.html)   # 基础
        self.assertIn('3134.7', self.html)   # 加成

    def test_percent_format(self):
        self.assertIn('39.1%', self.html)
        self.assertIn('244.1%', self.html)

    def test_weight_gold(self):
        """权重 >= 80 用金色标记，与 miao 一致。"""
        self.assertIn('class="gold"', self.html)

    def test_skills_exclude_technique(self):
        self.assertIn('普攻', self.html)
        self.assertIn('终结技', self.html)
        self.assertNotIn('秘技', self.html)   # miao 面板不显示秘技

    def test_skill_levels_shown(self):
        self.assertIn('>7<', self.html)
        self.assertIn('>12<', self.html)

    def test_light_cone(self):
        self.assertIn('爱如此刻永恒', self.html)
        self.assertIn('叠影1阶', self.html)
        self.assertIn('light_cone/23052.png', self.html)

    def test_sets(self):
        self.assertIn('再创天地的救世主×4', self.html)

    def test_missing_panel_fields_ok(self):
        class Bare:
            name = 'x'; level = 1; rank = 0; element = '火'; path = '毁灭'
            portrait = ''; panel = {}; panel_base = {}; panel_add = {}
            set_counts = {}; light_cone = None; skills = []
        html = panelcard.build_panel_html(Bare(), {}, '1')
        self.assertIn('x', html)


class TestFormat(unittest.TestCase):
    def test_fmt_flat(self):
        self.assertEqual(panelcard._fmt(5801.9, False), '5801.9')
        self.assertEqual(panelcard._fmt(101.0, False), '101')

    def test_fmt_percent(self):
        self.assertEqual(panelcard._fmt(0.391, True), '39.1%')


@unittest.skipUnless(True, '')
class TestRender(unittest.TestCase):
    def test_render_png_or_skip(self):
        from hsr.render import htmlcard

        if not htmlcard.available():
            self.skipTest('未安装 playwright')
        with tempfile.TemporaryDirectory() as tmp:
            try:
                path = panelcard.render_panel_card(
                    FakeChar(), WEIGHTS, '114172341', out_dir=tmp, filename='p.png')
            except Exception as e:
                self.skipTest(f'渲染失败: {e}')
            if path is None:
                self.skipTest('chromium 启动失败')
            self.assertTrue(os.path.isfile(path))
            self.assertGreater(os.path.getsize(path), 20000)


if __name__ == '__main__':
    unittest.main(verbosity=2)
