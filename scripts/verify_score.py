# -*- coding: utf-8 -*-
"""用真实账号数据验证评分引擎。"""

import os
import sys

SERVICE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'service')
sys.path.insert(0, SERVICE)

from hsr.api.mihomo import fetch_player
from hsr.core.artifact import score_set, improvement_hint

UID = '114172341'

player = fetch_player(UID)
print(f'账号: {player.nickname}  UID {player.uid}  Lv{player.level}')
print(f'展柜: {len(player.characters)} 人')
print()

for ch in player.characters:
    if not ch.artifacts:
        print(f'--- {ch.name}: 无遗器数据 ---')
        continue
    rep = score_set(ch.name, ch.artifacts, ch.base_attr)
    print('=' * 70)
    print(f'{ch.name}  {ch.element}/{ch.path}  星魂{ch.rank}  Lv{ch.level}')
    print(f'  套装: {ch.set_counts}')
    print(f'  总分 {rep.total:.1f} / 均分 {rep.average:.1f} → {rep.grade}   (模板 {rep.title})')
    print(f'  权重: { {k: v for k, v in rep.weight.items() if v} }')
    for p in rep.pieces:
        print(f'    {p.pos_name}({p.name})  {p.score:5.1f}  {p.grade:3s}  主:{p.main_title} {p.main_value:.1f} (权重{p.main_weight})')
        for r in p.sub_rows:
            flag = '  ← 无效' if r['useless'] else ('  ← 低' if r['weight'] < 75 else '')
            unit = '%' if r['percent'] else ''
            print(f'        {r["title"]:<8s} {r["value"]:7.1f}{unit}  权重{r["weight"]:<4}{flag}')
    print('  建议:')
    for h in improvement_hint(rep):
        print(f'    - {h}')
