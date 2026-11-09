# -*- coding: utf-8 -*-
"""复刻版评分卡测试（结构 + 真实截图）。"""

import os
import sys
import tempfile
import unittest

SERVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'service')
sys.path.insert(0, SERVICE)

from hsr.core.artifact import Artifact, SubAffix, score_set  # noqa: E402
from hsr.render import artiscard  # noqa: E402


class FakeChar:
    name = '昔涟'
    level = 80
    rank = 6
    element = '冰'
    path = '记忆'
    portrait = 'image/character_portrait/1415.png'


def make_report():
    arts = [
        Artifact(pos=1, name='救世主的登程风帽', set_name='再创天地的救世主',
                 main_key='hpPlus', main_value=705.6, icon='icon/relic/127_0.png',
                 level=15, subs=[SubAffix('hp', 7.8), SubAffix('speed', 6.6),
                                 SubAffix('cdmg', 11.0), SubAffix('effPct', 3.5)]),
        Artifact(pos=3, name='救世主的传承战袍', set_name='再创天地的救世主',
                 main_key='cdmg', main_value=64.8, icon='icon/relic/127_2.png',
                 level=15, subs=[SubAffix('hp', 8.2), SubAffix('speed', 8.6)]),
        Artifact(pos=6, name='翁法罗斯的永恒诗篇', set_name='永恒之地翁法罗斯',
                 main_key='hp', main_value=43.2, icon='icon/relic/323_3.png',
                 level=15, subs=[SubAffix('speed', 4.9), SubAffix('cpct', 9.1)]),
    ]
    return score_set('昔涟', arts, {'hp': 2667.0, 'atk': 922.0, 'def': 1045.0})


class TestBuildArtifactHtml(unittest.TestCase):
    def setUp(self):
        self.report = make_report()
        self.html = artiscard.build_artifact_html(FakeChar(), self.report, '114172341')

    def test_has_character_block(self):
        self.assertIn('昔涟', self.html)
        self.assertIn('UID 114172341', self.html)
        self.assertIn('6命', self.html)

    def test_has_portrait_background(self):
        self.assertIn('character_portrait/1415.png', self.html)

    def test_has_relic_icons(self):
        self.assertIn('icon/relic/127_0.png', self.html)

    def test_grade_color_matches_miao(self):
        # miao 的 ACE 是红色
        self.assertIn(artiscard.GRADE_COLOR['ACE'], self.html)

    def test_useless_stat_marked(self):
        """效果命中对昔涟权重为 0，应落到 nouse 类。"""
        self.assertIn('class="nouse"', self.html)

    def test_great_stat_marked(self):
        self.assertIn('class="great"', self.html)

    def test_total_score_present(self):
        self.assertIn(f'{self.report.total:.1f}', self.html)
        self.assertIn(self.report.grade, self.html)

    def test_fixed_positions_show_dash(self):
        """头/手主词条固定，分数列显示 -。"""
        self.assertIn('<span class="mark">-</span>', self.html)


class TestFormatHelpers(unittest.TestCase):
    def test_fmt_num_strips_zero(self):
        self.assertEqual(artiscard._fmt_num(25.0), '25')
        self.assertEqual(artiscard._fmt_num(25.032), '25')
        self.assertEqual(artiscard._fmt_num(42.3376), '42.3')

    def test_fmt_num_percent(self):
        self.assertEqual(artiscard._fmt_num(0.123, percent=True), '0.1%')

    def test_fmt_val_signed(self):
        self.assertEqual(artiscard._fmt_val(6.6, False), '+6.6')
        self.assertEqual(artiscard._fmt_val(7.8, True), '+7.8%')

    def test_relic_class(self):
        # 与 miao 一致：只有 great / nouse 加类，普通词条用默认白色
        self.assertEqual(artiscard._relic_class(100), 'great')
        self.assertEqual(artiscard._relic_class(50), '')
        self.assertEqual(artiscard._relic_class(0), 'nouse')


@unittest.skipUnless(artiscard.render_artifact_card, '无渲染器')
class TestRender(unittest.TestCase):
    def test_render_png_or_skip(self):
        from hsr.render import htmlcard

        if not htmlcard.available():
            self.skipTest('未安装 playwright')
        with tempfile.TemporaryDirectory() as tmp:
            try:
                path = artiscard.render_artifact_card(
                    FakeChar(), make_report(), '114172341',
                    out_dir=tmp, filename='a.png')
            except Exception as e:  # 无网络时图片加载失败
                self.skipTest(f'渲染失败（可能无网络）: {e}')
            if path is None:
                self.skipTest('chromium 启动失败')
            self.assertTrue(os.path.isfile(path))
            self.assertGreater(os.path.getsize(path), 20000)


if __name__ == '__main__':
    unittest.main(verbosity=2)
