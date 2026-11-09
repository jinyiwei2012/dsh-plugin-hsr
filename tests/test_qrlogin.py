# -*- coding: utf-8 -*-
"""扫码登录的单元测试（不联网，用固定样例）。"""

import os
import sys
import unittest

SERVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'service')
sys.path.insert(0, SERVICE)

from hsr.api import qrlogin  # noqa: E402


def confirmed_status(tokens, user_info=None):
    return qrlogin.QRStatus(
        status='Confirmed',
        tokens=tokens,
        user_info=user_info or {},
    )


class TestBuildCookie(unittest.TestCase):
    def test_standard_token_mapping(self):
        st = confirmed_status(
            [
                {'token_type': 2, 'token': 'LT123'},
                {'token_type': 3, 'token': 'CT456'},
                {'token_type': 1, 'token': 'ST789'},
            ],
            {'aid': '100000001'},
        )
        cookie = qrlogin.build_cookie(st)
        self.assertIn('ltoken=LT123', cookie)
        self.assertIn('cookie_token=CT456', cookie)
        self.assertIn('stoken=ST789', cookie)
        self.assertIn('ltuid=100000001', cookie)

    def test_missing_ltoken_raises(self):
        st = confirmed_status([{'token_type': 3, 'token': 'CT456'}], {'aid': '1'})
        with self.assertRaises(qrlogin.QRLoginError) as ctx:
            qrlogin.build_cookie(st)
        self.assertIn('ltoken', str(ctx.exception))

    def test_not_confirmed_raises(self):
        st = qrlogin.QRStatus(status='Created')
        with self.assertRaises(qrlogin.QRLoginError):
            qrlogin.build_cookie(st)

    def test_parse_cookie_roundtrip(self):
        """构造出的 Cookie 必须能被 mys.parse_cookie 识别。"""
        from hsr.api.mys import parse_cookie

        st = confirmed_status(
            [{'token_type': 2, 'token': 'LT'}, {'token_type': 3, 'token': 'CT'}],
            {'aid': '100000001'},
        )
        cookie = qrlogin.build_cookie(st)
        parsed = parse_cookie(cookie)
        self.assertTrue(parsed.usable, '构造出的 Cookie 应可用')
        self.assertEqual(parsed.ltoken, 'LT')
        self.assertEqual(parsed.ltuid, '100000001')


class TestStatusFlags(unittest.TestCase):
    def test_confirmed(self):
        self.assertTrue(qrlogin.QRStatus(status='Confirmed').confirmed)
        self.assertFalse(qrlogin.QRStatus(status='Created').confirmed)

    def test_expired_variants(self):
        for s in ('Expired', 'Invalid', 'Cancelled', 'Canceled'):
            self.assertTrue(qrlogin.QRStatus(status=s).expired, s)

    def test_status_case_insensitive(self):
        self.assertTrue(qrlogin.QRStatus(status='confirmed').confirmed)


class TestQRRender(unittest.TestCase):
    def test_available_returns_bool(self):
        self.assertIsInstance(qrlogin.qr_available(), bool)

    def test_render_without_library_returns_none(self):
        """没有二维码库时返回 None，不应抛异常。"""
        if qrlogin.qr_available():
            self.skipTest('本机已装二维码库')
        self.assertIsNone(qrlogin.render_qr_png('https://example.com', os.devnull))


if __name__ == '__main__':
    unittest.main(verbosity=2)
