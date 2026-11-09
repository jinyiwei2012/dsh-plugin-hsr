# -*- coding: utf-8 -*-
"""命令分发层：CLI 与服务端共用同一套实现。

支持的命令
----------
    查询 / 面板          账号概览
    练度                全角色遗器评分排行
    <角色>面板          单角色面板
    <角色>遗器          单角色遗器逐件评分
    帮助                命令说明

数据来源优先用米游社 Cookie（全部角色），没有绑定时回退 mihomo（仅展柜）。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable

from .api import mihomo
from .core.artifact import improvement_hint, score_set
from .data.attr_meta import ATTR_MAP, POS_NAMES
from .store import db

HELP_TEXT = """星穹铁道查询 · 命令

  查询 / 面板        账号概览（等级、角色数、遗器评分总览）
  练度               全角色遗器评分排行
  <角色>面板         单角色面板（等级/星魂/光锥/关键属性）
  <角色>遗器         单角色遗器逐件评分与提升建议
  混沌 / 虚构 / 末日  战绩（需要 Cookie）
  帮助               显示本说明

绑定 Cookie 才能查到全部角色与战绩（否则只有游戏展柜里展示的那几个）：
  python service/tools/bind_cookie.py
"""

# 面板里值得展示的属性
PANEL_KEYS = [
    ('生命值', '生命'),
    ('攻击力', '攻击'),
    ('防御力', '防御'),
    ('速度', '速度'),
    ('暴击率', '暴击'),
    ('暴击伤害', '暴伤'),
    ('击破特攻', '击破'),
    ('效果命中', '命中'),
    ('效果抵抗', '抵抗'),
    ('能量恢复效率', '充能'),
]


@dataclass
class CommandResult:
    """一条命令的执行结果。"""

    ok: bool
    title: str
    lines: list[str] = field(default_factory=list)
    # 结构化数据（出图 / 前端用）
    data: dict[str, Any] = field(default_factory=dict)
    # 出图用：卡片标题 / 副标题 / 区块
    card_title: str = ''
    card_subtitle: str = ''
    blocks: list[Any] = field(default_factory=list)

    @property
    def text(self) -> str:
        return '\n'.join([self.title] + self.lines if self.title else self.lines)

    def render_png(self) -> str | None:
        """渲染成 PNG；Pillow 不可用或没有区块时返回 None。"""
        if not self.blocks:
            return None
        from .render import card as card_render

        return card_render.render_card(
            title=self.card_title or self.title or '星穹铁道',
            subtitle=self.card_subtitle,
            blocks=self.blocks,
            footer='dsh-plugin-hsr · 词条权重来自 miao-plugin',
        )


def _fmt_panel(panel: dict[str, float]) -> list[str]:
    """把面板字典格式化成一行行文字。"""
    out = []
    for raw_key, label in PANEL_KEYS:
        v = panel.get(raw_key)
        if v is None:
            continue
        # 这些是百分比属性
        if raw_key in ('暴击率', '暴击伤害', '击破特攻', '效果命中', '效果抵抗', '能量恢复效率'):
            out.append(f'{label} {v * 100:.1f}%')
        else:
            out.append(f'{label} {v:.0f}')
    return out


def _resolve_char(player: mihomo.Player, name: str) -> mihomo.Character | None:
    """按名字或 id 找角色。"""
    name = name.strip()
    for c in player.characters:
        if c.name == name or c.id == name:
            return c
    # 宽松匹配：包含关系
    cands = [c for c in player.characters if name and name in c.name]
    if len(cands) == 1:
        return cands[0]
    return None


def _get_player(uid: str | None, refresh: bool = False) -> mihomo.Player:
    """取账号数据（带缓存）。

    有 cookie 时优先走米游社（全部角色）；否则走 mihomo（仅展柜）。
    当前实现统一用 mihomo 拉取，米游社通道见 api/mys.py。
    """
    account = db.get_account(uid)
    real_uid = account.uid if account else (uid or db.get_default_uid())
    if not real_uid:
        raise RuntimeError(
            '还没有绑定账号。先运行 `python service/tools/bind_cookie.py --uid-only <UID>`'
            '（仅查展柜）或 `python service/tools/bind_cookie.py`（绑 Cookie 查全部）'
        )

    if not refresh:
        cached = db.load_profile(real_uid, max_age=600)
        if cached and cached.get('_source') == 'mihomo':
            return _player_from_dict(cached)

    player = mihomo.fetch_player(real_uid)
    db.save_profile(real_uid, _player_to_dict(player))
    return player


def _player_to_dict(p: mihomo.Player) -> dict[str, Any]:
    """序列化以便缓存。"""
    return {
        '_source': 'mihomo',
        'uid': p.uid,
        'nickname': p.nickname,
        'level': p.level,
        'world_level': p.world_level,
        'signature': p.signature,
        'avatar_name': p.avatar_name,
        'stats': p.stats,
        'characters': [
            {
                'id': c.id, 'name': c.name, 'rarity': c.rarity, 'rank': c.rank,
                'level': c.level, 'path': c.path, 'element': c.element,
                'base_attr': c.base_attr, 'panel': c.panel,
                'light_cone': c.light_cone, 'set_counts': c.set_counts,
                'skills': c.skills,
                'artifacts': [
                    {
                        'pos': a.pos, 'name': a.name, 'set_name': a.set_name,
                        'level': a.level, 'rarity': a.rarity,
                        'main_key': a.main_key, 'main_value': a.main_value,
                        'main_name': a.main_name,
                        'subs': [
                            {'key': s.key, 'value': s.value, 'count': s.count, 'name': s.name}
                            for s in a.subs
                        ],
                    }
                    for a in c.artifacts
                ],
            }
            for c in p.characters
        ],
    }


def _player_from_dict(d: dict[str, Any]) -> mihomo.Player:
    """从缓存还原。"""
    from .core.artifact import Artifact, SubAffix

    chars = []
    for c in d.get('characters') or []:
        arts = [
            Artifact(
                pos=a['pos'], name=a.get('name', ''), set_name=a.get('set_name', ''),
                level=a.get('level', 0), rarity=a.get('rarity', 5),
                main_key=a.get('main_key', ''), main_value=a.get('main_value', 0.0),
                main_name=a.get('main_name', ''),
                subs=[SubAffix(**s) for s in a.get('subs') or []],
            )
            for a in c.get('artifacts') or []
        ]
        chars.append(mihomo.Character(
            id=c['id'], name=c['name'], rarity=c.get('rarity', 5),
            rank=c.get('rank', 0), level=c.get('level', 1),
            path=c.get('path', ''), element=c.get('element', ''),
            base_attr=c.get('base_attr') or {}, light_cone=c.get('light_cone'),
            artifacts=arts, set_counts=c.get('set_counts') or {},
            skills=c.get('skills') or [], panel=c.get('panel') or {},
        ))
    return mihomo.Player(
        uid=d['uid'], nickname=d.get('nickname', ''), level=d.get('level', 0),
        world_level=d.get('world_level', 0), signature=d.get('signature', ''),
        avatar_id='', avatar_name=d.get('avatar_name', ''),
        stats=d.get('stats') or {}, characters=chars,
    )


# ------------------------------------------------------------------ 具体命令

def cmd_overview(uid: str | None = None) -> CommandResult:
    from .render.card import Block, grade_color

    p = _get_player(uid)
    st = p.stats
    lines = [
        f'UID {p.uid}  {p.nickname}',
        f'开拓等级 {p.level}  世界等级 {p.world_level}',
    ]
    if p.signature:
        lines.append(f'签名 {p.signature}')
    lines.append('')
    lines.append(f'角色数 {st.get("avatar_count", "?")}  '
                 f'光锥 {st.get("light_cone_count", "?")}  '
                 f'遗器 {st.get("relic_count", "?")}')
    lines.append(f'成就 {st.get("achievement_count", "?")}  '
                 f'模拟宇宙 {st.get("universe_level", "?")}')
    lines.append('')
    lines.append(f'本页可见角色 {len(p.characters)} 人'
                 + ('（mihomo 只返回展柜角色，绑定 Cookie 可查全部）' if len(p.characters) < 20 else ''))

    blocks = [Block(heading='账号', rows=[
        ('等级', f'{p.level}  世界 {p.world_level}', None),
        ('角色 / 光锥 / 遗器',
         f'{st.get("avatar_count", "?")} / {st.get("light_cone_count", "?")} / {st.get("relic_count", "?")}', None),
        ('成就', str(st.get('achievement_count', '?')), None),
    ])]

    if p.characters:
        lines.append('')
        lines.append('遗器评分：')
        rows = []
        for c in p.characters:
            if not c.artifacts:
                continue
            rep = score_set(c.name, c.artifacts, c.base_attr)
            rows.append((c.name, rep.average, rep.grade))
        rows.sort(key=lambda x: -x[1])
        for name, avg, grade in rows:
            lines.append(f'  {name:<8s} {avg:5.1f}  {grade}')
        blocks.append(Block(heading='遗器评分', rows=[
            (name, f'{avg:.1f}  {grade}', grade_color(grade))
            for name, avg, grade in rows
        ]))

    if len(p.characters) < 20:
        blocks.append(Block(text='当前数据来自 mihomo 公开接口，只有游戏展柜里的角色。'
                                 '绑定米游社 Cookie 后可查询账号下全部角色。'))

    return CommandResult(
        ok=True, title='星穹铁道 · 账号概览', lines=lines, blocks=blocks,
        card_title='星穹铁道 · 账号概览',
        card_subtitle=f'{p.nickname}  UID {p.uid}',
    )


def cmd_rank(uid: str | None = None) -> CommandResult:
    from .render.card import Block, grade_color

    p = _get_player(uid)
    rows = []
    for c in p.characters:
        rep = score_set(c.name, c.artifacts, c.base_attr) if c.artifacts else None
        rows.append((c.name, c.element, c.level, c.rank, rep))
    rows.sort(key=lambda r: -(r[4].average if r[4] else -1))

    lines = [f'共 {len(rows)} 名可见角色（按遗器均分排序）', '']
    card_rows = []
    for name, elem, lvl, rank, rep in rows:
        if rep:
            lines.append(f'{name:<8s} Lv{lvl} {elem} 星魂{rank}  '
                         f'{rep.average:5.1f} {rep.grade:<4s} '
                         f'({len(rep.pieces)}/6 件)')
            card_rows.append((f'{name}  Lv{lvl} {elem}',
                              f'{rep.average:.1f}  {rep.grade}',
                              grade_color(rep.grade)))
        else:
            lines.append(f'{name:<8s} Lv{lvl} {elem} 星魂{rank}  无遗器')

    blocks = [Block(heading='遗器评分排行', rows=card_rows)]
    return CommandResult(
        ok=True, title='星穹铁道 · 练度排行', lines=lines, blocks=blocks,
        card_title='星穹铁道 · 练度排行',
        card_subtitle=f'{p.nickname}  UID {p.uid}  ·  {len(rows)} 名可见角色',
    )


def cmd_panel(uid: str | None, char_name: str) -> CommandResult:
    from .render.card import Block, TEXT_WARN, grade_color

    p = _get_player(uid)
    c = _resolve_char(p, char_name)
    if not c:
        names = '、'.join(x.name for x in p.characters[:12])
        return CommandResult(False, f'找不到角色「{char_name}」',
                             [f'可见角色：{names}',
                              '（mihomo 只返回展柜角色，绑定 Cookie 可查全部）'])

    lines = [f'{c.name}  {c.rarity}★  {c.element}/{c.path}',
             f'等级 {c.level}  星魂 {c.rank}']
    if c.light_cone:
        lc = c.light_cone
        lines.append(f'光锥 {lc["name"]}  {lc["rarity"]}★ 叠影{lc["rank"]} Lv{lc["level"]}')
    if c.set_counts:
        sets = '  '.join(f'{k}×{v}' for k, v in c.set_counts.items())
        lines.append(f'套装 {sets}')

    blocks = [Block(heading='基础', rows=[
        ('等级 / 星魂', f'Lv{c.level}  {c.rank} 星魂', None),
        ('命途 / 属性', f'{c.path} / {c.element}', None),
        ('光锥', (f'{c.light_cone["name"]}  R{c.light_cone["rank"]}'
                  if c.light_cone else '无'), None),
        ('套装', '  '.join(f'{k}×{v}' for k, v in c.set_counts.items()) or '无', None),
    ])]

    lines.append('')
    panel = _fmt_panel(c.panel)
    if panel:
        lines.append('面板（含养成加成）：')
        for i in range(0, len(panel), 3):
            lines.append('  ' + '   '.join(panel[i:i + 3]))
        blocks.append(Block(heading='面板', rows=[
            (lbl, val, None) for lbl, val in (item.split(' ', 1) for item in panel)
        ]))

    if c.skills:
        lines.append('')
        lines.append('技能：')
        sk = '  '.join(f'{s["type"]}{s["level"]}' for s in c.skills if s['level'] > 0)
        lines.append('  ' + sk)

    if c.artifacts:
        rep = score_set(c.name, c.artifacts, c.base_attr)
        lines.append('')
        lines.append(f'遗器 {rep.average:.1f} 分 / {rep.grade}（模板 {rep.title}）')
        blocks.append(Block(
            heading='遗器',
            badge=f'{rep.average:.1f}  {rep.grade}',
            badge_color=grade_color(rep.grade),
        ))
        for pc in rep.pieces:
            blocks.append(Block(
                heading=f'{pc.pos_name} {pc.name}',
                badge=f'{pc.score:.1f}  {pc.grade}',
                badge_color=grade_color(pc.grade),
                rows=[(r['title'],
                       f'{r["value"]:.1f}{"%" if r["percent"] else ""}',
                       TEXT_WARN if r['useless'] else None)
                      for r in pc.sub_rows],
            ))

    return CommandResult(
        ok=True, title='', lines=lines, blocks=blocks,
        card_title=f'{c.name}  {c.element}/{c.path}',
        card_subtitle=f'Lv{c.level}  {c.rank} 星魂  UID {p.uid}',
    )


def cmd_artifacts(uid: str | None, char_name: str) -> CommandResult:
    from .render.card import Block, TEXT_WARN, grade_color

    p = _get_player(uid)
    c = _resolve_char(p, char_name)
    if not c:
        return CommandResult(False, f'找不到角色「{char_name}」')
    if not c.artifacts:
        return CommandResult(False, f'{c.name} 没有遗器数据')

    rep = score_set(c.name, c.artifacts, c.base_attr)
    lines = [
        f'{c.name}  {c.element}/{c.path}  星魂{c.rank}',
        f'遗器总分 {rep.total:.1f} / 均分 {rep.average:.1f} → {rep.grade}',
        f'评分模板 {rep.title}',
        '',
    ]

    w = {k: v for k, v in rep.weight.items() if v}
    weight_text = '  '.join(f'{k}{v}' for k, v in w.items())
    lines.append('词条权重：' + weight_text)
    lines.append('')

    blocks = [Block(
        heading='总览',
        badge=f'{rep.average:.1f}  {rep.grade}',
        badge_color=grade_color(rep.grade),
        rows=[
            ('总分', f'{rep.total:.1f}', None),
            ('均分（按 6 件折算）', f'{rep.average:.1f}', None),
            ('已装备', f'{len(rep.pieces)} / 6 件', None),
        ],
        text='词条权重：' + weight_text,
    )]

    for pc in rep.pieces:
        lines.append(f'【{pc.pos_name}】{pc.name}  {pc.score:.1f} 分 / {pc.grade}')
        lines.append(f'    主词条 {pc.main_title} {pc.main_value:.1f}（权重 {pc.main_weight}）')
        rows = [('主词条', f'{pc.main_title} {pc.main_value:.1f}',
                 TEXT_WARN if pc.main_weight == 0 and pc.pos > 2 else None)]
        if pc.sub_rows:
            for r in pc.sub_rows:
                unit = '%' if r['percent'] else ''
                tag = ''
                if r['useless']:
                    tag = '  ✗ 无效'
                elif r['weight'] < 75:
                    tag = '  · 权重偏低'
                lines.append(f'    {r["title"]} {r["value"]:.1f}{unit}  权重{r["weight"]}{tag}')
                rows.append((f'{r["title"]}  (权重{r["weight"]})',
                             f'{r["value"]:.1f}{unit}',
                             TEXT_WARN if r['useless'] else None))
        else:
            lines.append('    (无副词条)')
        lines.append('')
        blocks.append(Block(
            heading=f'{pc.pos_name} {pc.name}',
            badge=f'{pc.score:.1f}  {pc.grade}',
            badge_color=grade_color(pc.grade),
            rows=rows,
        ))

    hints = improvement_hint(rep)
    if hints:
        lines.append('提升建议：')
        lines.extend('  ' + h for h in hints)
        blocks.append(Block(heading='提升建议', text='\n'.join(hints)))

    return CommandResult(
        ok=True, title='', lines=lines, blocks=blocks,
        card_title=f'{c.name} · 遗器评分',
        card_subtitle=f'{rep.total:.1f} 分 / 均分 {rep.average:.1f} → {rep.grade}  ·  {rep.title}',
    )


# ------------------------------------------------------------------ 战绩

CHALLENGE_KINDS = {
    '混沌': '1', '混沌回忆': '1', '深渊': '1',
    '虚构': '2', '虚构叙事': '2',
    '末日': '3', '末日幻影': '3',
}


def _fmt_time(t: dict | None) -> str:
    if not isinstance(t, dict):
        return ''
    for k in ('datetime', 'date', 'timestamp'):
        if t.get(k):
            return str(t[k])
    return ''


def cmd_challenge(uid: str | None, kind: str = '1') -> CommandResult:
    """战绩查询（需要米游社 Cookie）。"""
    from .api import mys

    account = db.get_account(uid) or db.get_account(None)
    if not account or not account.cookie:
        return CommandResult(
            False, '战绩查询需要米游社 Cookie',
            [
                'mihomo 公开接口不提供战绩数据。',
                '绑定方法：',
                '  python service/tools/bind_cookie.py',
                '获取 Cookie 的步骤见 docs/cookie.md',
            ],
        )

    parsed = mys.parse_cookie(account.cookie)
    try:
        data = mys.fetch_challenge(account.uid, account.server, parsed, kind)
    except mys.MysError as e:
        return CommandResult(False, '战绩查询失败', [str(e)])

    if not data or data.get('has_data') is False:
        return CommandResult(
            True, '暂无本期战绩',
            ['本期还没有记录，或者尚未通关。'],
        )

    star = data.get('star_num')
    max_floor = data.get('max_floor')
    battle = data.get('battle_num')
    lines = [
        f'本期 星数 {star}' if star is not None else '',
        f'最高层 {max_floor}  战斗次数 {battle}' if max_floor else '',
        f'时间 {_fmt_time(data.get("begin_time"))} ~ {_fmt_time(data.get("end_time"))}',
        '',
    ]
    lines = [ln for ln in lines if ln is not None]

    for floor in data.get('all_floor_detail') or []:
        name = floor.get('name') or '层'
        fl = floor.get('floor') or ''
        st = floor.get('star_num')
        lines.append(f'{name} {fl}  星 {st}')
        for node_key in ('node_1', 'node_2', 'node_3'):
            node = floor.get(node_key)
            if not isinstance(node, dict):
                continue
            avatars = node.get('avatars') or []
            if avatars:
                names = '、'.join(
                    f'{a.get("name") or a.get("id")} Lv{a.get("level")}' for a in avatars
                )
                lines.append(f'    {names}')

    title = {
        '1': '混沌回忆', '2': '虚构叙事', '3': '末日幻影',
    }.get(kind, '战绩')
    return CommandResult(
        ok=True, title=f'星穹铁道 · {title}', lines=lines,
        card_title=f'星穹铁道 · {title}',
        card_subtitle=f'{account.nickname or account.uid}',
    )


# ------------------------------------------------------------------ 分发

CHAR_SUFFIX = re.compile(r'^(.+?)(面板|遗器|遗物|评分)$')


def dispatch(command: str) -> CommandResult:
    """解析并执行一条命令。"""
    raw = (command or '').strip()
    # 去掉可能的前缀
    for pfx in ('hsr', 'ww', 'sr', '#', '/hsr', '/sr'):
        if raw.lower().startswith(pfx):
            raw = raw[len(pfx):].strip()
            break
    if not raw:
        return CommandResult(True, '', HELP_TEXT.splitlines())

    low = raw.lower()

    if low in ('帮助', 'help', '?', '？'):
        return CommandResult(True, '', HELP_TEXT.splitlines())
    if low in ('查询', '面板', '概览', '账号', 'info'):
        return cmd_overview()
    if low in ('练度', '排行', '遗器排行', 'rank'):
        return cmd_rank()
    if low in CHALLENGE_KINDS:
        return cmd_challenge(None, CHALLENGE_KINDS[low])
    if low in ('战绩', '深渊战绩'):
        return cmd_challenge(None, '1')

    m = CHAR_SUFFIX.match(raw)
    if m:
        name, kind = m.group(1), m.group(2)
        if kind in ('遗器', '遗物', '评分'):
            return cmd_artifacts(None, name)
        return cmd_panel(None, name)

    return CommandResult(False, f'无法识别的命令：{raw}',
                         HELP_TEXT.splitlines())
