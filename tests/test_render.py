# -*- coding: utf-8 -*-
"""出图模块测试。

程序缺失 Pillow 时相关用例自动跳过，不影响其它测试。
"""

import os
import sys
import tempfile
import unittest

SERVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'service')
sys.path.insert(0, SERVICE)

from hsr.render import card  # noqa: E402


@unittest.skipUnless(card.available(), 'Pillow 或中文字体不可用')
class TestRender(unittest.TestCase):
    def test_render_basic_card(self):
        blocks = [
            card.Block(heading='基础', rows=[('等级', '70', None), ('角色数', '100', None)]),
            card.Block(heading='遗器评分', badge='52.4  ACE',
                       badge_color=card.grade_color('ACE'),
                       rows=[('昔涟', '52.4  ACE', card.grade_color('ACE'))]),
            card.Block(heading='建议', text='无效词条：效果命中、大攻击'),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = card.render_card('测试标题', '副标题', blocks, out_dir=tmp,
                                    filename='test.png')
            self.assertIsNotNone(path)
            self.assertTrue(os.path.isfile(path))
            self.assertGreater(os.path.getsize(path), 1000)
            with open(path, 'rb') as f:
                self.assertEqual(f.read(8), b'\x89PNG\r\n\x1a\n')

    def test_render_long_text_wraps(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmp:
            short = card.render_card(
                '换行', '', [card.Block(heading='文本', text='短')],
                out_dir=tmp, filename='short.png',
            )
            long = card.render_card(
                '换行', '', [card.Block(heading='文本', text='测试自动换行。' * 60)],
                out_dir=tmp, filename='long.png',
            )
            self.assertIsNotNone(short)
            self.assertIsNotNone(long)
            with Image.open(short) as a, Image.open(long) as b:
                # 长文本必须显著撑高卡片，说明换行生效
                self.assertGreater(b.height, a.height + 80,
                                   f'长文本未撑高: {a.height} -> {b.height}')

    def test_empty_blocks_still_renders(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = card.render_card('空卡片', '', [], out_dir=tmp, filename='empty.png')
            self.assertIsNotNone(path)
            self.assertTrue(os.path.isfile(path))

    def test_grade_color_known(self):
        self.assertEqual(card.grade_color('ACE'), card.GRADE_COLOR['ACE'])
        # 未知评级回退到正文色
        self.assertEqual(card.grade_color('???'), card.TEXT)


class TestRenderUnavailable(unittest.TestCase):
    def test_available_returns_bool(self):
        self.assertIsInstance(card.available(), bool)


if __name__ == '__main__':
    unittest.main(verbosity=2)
