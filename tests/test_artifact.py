# -*- coding: utf-8 -*-
"""遗器评分引擎单元测试。

运行: python -m pytest tests/ -q
或:   python tests/test_artifact.py
"""

import os
import sys
import unittest

SERVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'service')
sys.path.insert(0, SERVICE)

from hsr.core.artifact import (  # noqa: E402
    Artifact,
    SubAffix,
    improvement_hint,
    make_char_cfg,
    score_set,
)
from hsr.data.attr_meta import affix_to_key, element_field_of, mark_class  # noqa: E402
from hsr.data.useful_attr import USEFUL_ATTR, get_useful_attr  # noqa: E402


def make_six(subs_by_pos=None, main_by_pos=None):
    """构造一整套 6 件遗器用于测试。"""
    subs_by_pos = subs_by_pos or {}
    main_by_pos = main_by_pos or {}
    out = []
    defaults = {
        1: ('hpPlus', 705.6),
        2: ('atkPlus', 352.8),
        3: ('cdmg', 64.8),
        4: ('speed', 25.0),
        5: ('dmg', 38.9),
        6: ('atk', 43.2),
    }
    for pos in range(1, 7):
        key, val = main_by_pos.get(pos, defaults[pos])
        out.append(Artifact(
            pos=pos,
            name=f'测试{pos}',
            set_name='测试套',
            main_key=key,
            main_value=val,
            subs=subs_by_pos.get(pos, []),
        ))
    return out


class TestAttrMeta(unittest.TestCase):
    def test_mark_class_boundaries(self):
        # 与 miao 一致：score < 阈值 才落到该档
        # D[0,7) C[7,14) B[14,21) A[21,28) S[28,35)
        # SS[35,42) SSS[42,49) ACE[49,56) MAX[56,70]
        self.assertEqual(mark_class(0), 'D')
        self.assertEqual(mark_class(6.9), 'D')
        self.assertEqual(mark_class(7), 'C')
        self.assertEqual(mark_class(20.9), 'B')
        self.assertEqual(mark_class(21), 'A')
        self.assertEqual(mark_class(27.9), 'A')
        self.assertEqual(mark_class(28), 'S')
        self.assertEqual(mark_class(34.9), 'S')
        self.assertEqual(mark_class(35), 'SS')
        self.assertEqual(mark_class(42), 'SSS')
        self.assertEqual(mark_class(49), 'ACE')
        self.assertEqual(mark_class(56), 'MAX')
        self.assertEqual(mark_class(70), 'MAX')

    def test_element_field_mapping(self):
        # 雷是 thunder_dmg，历史上有 lightning_dmg 写法
        self.assertEqual(element_field_of('ThunderAddedRatio', 'thunder_dmg'), 'thunder_dmg')
        self.assertEqual(element_field_of('LightningAddedRatio', ''), 'thunder_dmg')
        self.assertEqual(element_field_of('IceAddedRatio', 'ice_dmg'), 'ice_dmg')
        self.assertEqual(element_field_of('AttackAddedRatio', 'atk'), '')

    def test_affix_to_key(self):
        self.assertEqual(affix_to_key('HPDelta'), 'hpPlus')
        self.assertEqual(affix_to_key('HPAddedRatio'), 'hp')
        self.assertEqual(affix_to_key('CriticalChanceBase'), 'cpct')
        self.assertEqual(affix_to_key('ThunderAddedRatio', 'thunder_dmg'), 'dmg')
        self.assertEqual(affix_to_key('Unknown'), '')


class TestWeightTable(unittest.TestCase):
    def test_table_loaded(self):
        self.assertGreater(len(USEFUL_ATTR), 100, '权重表应包含全部星铁角色')

    def test_known_characters(self):
        # 流萤是击破角色：不要双暴，要击破特攻
        liuying = get_useful_attr('流萤')
        self.assertEqual(liuying['cpct'], 0)
        self.assertEqual(liuying['cdmg'], 0)
        self.assertEqual(liuying['stance'], 100)

        # 风堇是奶妈：不要击破特攻
        fengjin = get_useful_attr('风堇')
        self.assertEqual(fengjin['stance'], 0)
        self.assertEqual(fengjin['heal'], 100)

        # 云璃是物理输出：不要防御
        yunli = get_useful_attr('云璃')
        self.assertEqual(yunli['def'], 0)
        self.assertEqual(yunli['cpct'], 100)

    def test_unknown_returns_empty(self):
        self.assertEqual(get_useful_attr('不存在的角色'), {})


class TestScoring(unittest.TestCase):
    def test_score_in_range(self):
        cfg = make_char_cfg('昔涟')
        arts = make_six({
            pos: [SubAffix('cpct', 9.72), SubAffix('cdmg', 21.6)]
            for pos in range(1, 7)
        })
        rep = score_set('昔涟', arts)
        for p in rep.pieces:
            self.assertGreaterEqual(p.score, 0.0)
            self.assertLessEqual(p.score, 70.0, f'{p.pos_name} 分数越界')

    def test_better_subs_score_higher(self):
        good = make_six({
            pos: [SubAffix('cpct', 9.72), SubAffix('cdmg', 21.6), SubAffix('speed', 6.6)]
            for pos in range(1, 7)
        })
        bad = make_six({
            pos: [SubAffix('def', 10.8), SubAffix('defPlus', 54.0)]
            for pos in range(1, 7)
        })
        g = score_set('昔涟', good)
        b = score_set('昔涟', bad)
        self.assertGreater(g.total, b.total, '有效词条应得分更高')

    def test_useless_sub_scores_zero(self):
        """对云璃来说防御权重为 0，纯防御副词条不该贡献分数。"""
        cfg = make_char_cfg('云璃')
        def_only = make_six({pos: [SubAffix('def', 10.8), SubAffix('defPlus', 54.0)] for pos in range(1, 7)})
        empty = make_six({pos: [] for pos in range(1, 7)})
        a = score_set('云璃', def_only)
        b = score_set('云璃', empty)
        # 防御词条几乎不加分（允许浮点误差）
        self.assertAlmostEqual(a.total, b.total, delta=0.5)

    def test_missing_piece_penalised(self):
        full = make_six({pos: [SubAffix('cpct', 9.72)] for pos in range(1, 7)})
        partial = [a for a in full if a.pos != 3]
        a = score_set('昔涟', full)
        b = score_set('昔涟', partial)
        # 缺一件：总分下降，且均分按 6 件折算
        self.assertLess(b.total, a.total)
        self.assertAlmostEqual(b.average, b.total / 6)

    def test_off_element_orb_penalised(self):
        """位面球属性与角色不符时主词条不计权。"""
        right = make_six(main_by_pos={5: ('dmg', 38.9)})
        wrong = make_six(main_by_pos={5: ('__elem__fire_dmg', 38.9)})
        a = score_set('昔涟', right)  # 昔涟是冰
        b = score_set('昔涟', wrong)
        self.assertGreater(a.total, b.total, '异色球应得分更低')

    def test_hints_report_useless(self):
        # 风堇不吃击破特攻：给她一个击破副词条，应被点名
        arts = make_six({
            pos: [SubAffix('cpct', 3.24)] for pos in range(1, 7)
        })
        arts[0] = Artifact(
            pos=1, name='测试头', set_name='测试套',
            main_key='hpPlus', main_value=705.6,
            subs=[SubAffix('stance', 16.8), SubAffix('speed', 9.1)],
        )
        rep = score_set('风堇', arts)
        hints = improvement_hint(rep)
        joined = '\n'.join(hints)
        self.assertIn('击破特攻', joined, f'应点名击破特攻无效，实际:\n{joined}')

    def test_fixed_main_not_warned(self):
        """头部/手部主词条固定，不该建议更换。"""
        arts = make_six()
        rep = score_set('黄泉', arts)  # 黄泉 hp 权重 0，头部小生命权重 0
        hints = improvement_hint(rep)
        self.assertFalse(
            any('头部 主词条' in h for h in hints),
            f'头部不应被建议更换，实际: {hints}',
        )


if __name__ == '__main__':
    unittest.main(verbosity=2)
