# -*- coding: utf-8 -*-
"""HTML 卡片渲染测试。"""

import os
import sys
import tempfile
import unittest

SERVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'service')
sys.path.insert(0, SERVICE)

from hsr.render import htmlcard  # noqa: E402
from hsr.render.card import Block, grade_color  # noqa: E402


class TestBuildHtml(unittest.TestCase):
    def test_contains_title_and_subtitle(self):
        html = htmlcard.build_html('标题', '副标题', [Block(heading='区块')])
        self.assertIn('标题', html)
        self.assertIn('副标题', html)
        self.assertIn('区块', html)
        self.assertIn('<!doctype html>', html)

    def test_escapes_html(self):
        html = htmlcard.build_html('<script>alert(1)</script>', '', [])
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_rows_rendered(self):
        b = Block(heading='面板', rows=[('速度', '180', None), ('暴击', '39.1%', (255, 0, 0))])
        html = htmlcard.build_html('t', '', [b])
        self.assertIn('速度', html)
        self.assertIn('180', html)
        self.assertIn('rgb(255,0,0)', html)

    def test_badge_color(self):
        b = Block(heading='x', badge='52.4 ACE', badge_color=grade_color('ACE'))
        html = htmlcard.build_html('t', '', [b])
        self.assertIn('52.4 ACE', html)
        self.assertIn('rgb(', html)

    def test_text_block_preserved(self):
        html = htmlcard.build_html('t', '', [Block(heading='建议', text='第一行\n第二行')])
        self.assertIn('第一行', html)
        self.assertIn('第二行', html)

    def test_empty_blocks_ok(self):
        html = htmlcard.build_html('只有标题', '', [])
        self.assertIn('只有标题', html)

    def test_footer_default(self):
        html = htmlcard.build_html('t', '', [])
        self.assertIn('生成于', html)


class TestAvailability(unittest.TestCase):
    def test_available_is_bool(self):
        self.assertIsInstance(htmlcard.available(), bool)


@unittest.skipUnless(htmlcard.available(), '未安装 playwright')
class TestPlaywrightRender(unittest.TestCase):
    def test_render_produces_png(self):
        blocks = [
            Block(heading='基础', rows=[('等级', '70', None)]),
            Block(heading='遗器', badge='52.4 ACE', badge_color=grade_color('ACE'),
                  rows=[('昔涟', '52.4 ACE', grade_color('ACE'))]),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            path = htmlcard.render_card('测试', '副标题', blocks,
                                        out_dir=tmp, filename='t.png')
            if path is None:
                self.skipTest('chromium 启动失败（可能未安装浏览器）')
            self.assertTrue(os.path.isfile(path))
            with open(path, 'rb') as f:
                self.assertEqual(f.read(8), b'\x89PNG\r\n\x1a\n')
            self.assertGreater(os.path.getsize(path), 5000)


if __name__ == '__main__':
    unittest.main(verbosity=2)
